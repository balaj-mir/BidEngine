import os
import re
import fitz  # PyMuPDF
from docx import Document
from typing import Dict, Any, List

class DocumentParser:
    def parse(self, filepath: str) -> Dict[str, Any]:
        """
        Parses a PDF or DOCX file, extracts text, identifies tables and sections, 
        and extracts metadata. Strips top/bottom 5% of pages to ignore header/footer.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        file_size = os.path.getsize(filepath)

        if ext == '.pdf':
            return self._parse_pdf(filepath, file_size)
        elif ext == '.docx':
            return self._parse_docx(filepath, file_size)
        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

    def _parse_pdf(self, filepath: str, file_size: int) -> Dict[str, Any]:
        try:
            doc = fitz.open(filepath)
        except Exception as e:
            if "encrypted" in str(e).lower() or "password" in str(e).lower():
                raise ValueError("Password-protected or encrypted PDF. Cannot parse.")
            raise ValueError(f"Failed to open PDF: {e}")

        pages = []
        full_text_list = []
        sections = []
        is_scanned = True
        title = doc.metadata.get("title") or os.path.basename(filepath)

        current_section = {"heading": "Introduction", "content": "", "page_start": 1, "page_end": 1}

        for i, page in enumerate(doc):
            page_num = i + 1
            # Get height and width
            rect = page.rect
            height = rect.height
            margin = height * 0.05  # 5% header/footer strip

            # Get text blocks
            blocks = page.get_text("blocks")
            page_text_blocks = []
            tables = []

            # Identify tables: PyMuPDF 1.24+ has page.find_tables()
            try:
                tabs = page.find_tables()
                for table in tabs:
                    # Convert to simple markdown
                    markdown_rows = []
                    for row in table.extract():
                        # filter out None
                        row_clean = [str(cell) if cell is not None else "" for cell in row]
                        markdown_rows.append("| " + " | ".join(row_clean) + " |")
                    if markdown_rows:
                        # add separator row
                        separator = "| " + " | ".join(["---"] * len(table.extract()[0])) + " |"
                        markdown_rows.insert(1, separator)
                        tables.append("\n".join(markdown_rows))
            except Exception:
                # Fallback if find_tables fails or not supported
                pass

            for b in blocks:
                # b = (x0, y0, x1, y1, "text", block_no, block_type)
                y0, y1 = b[1], b[3]
                text = b[4].strip()

                # Skip header/footer
                if y0 < margin or y1 > (height - margin):
                    continue

                if text:
                    page_text_blocks.append(text)
                    
                    # Detect potential section headings
                    # e.g., "1.0 INTRODUCTION", "SECTION IV - SCOPE", "ELIGIBILITY CRITERIA"
                    if len(text) < 100 and (
                        re.match(r'^(\d+\.\d*)\s+[A-Z]', text) or 
                        re.match(r'^(SECTION|CHAPTER)\s+[I|V|X|L|\d+]', text, re.IGNORECASE) or
                        (text.isupper() and len(text) > 4 and not text.startswith("http"))
                    ):
                        if current_section["content"].strip():
                            current_section["page_end"] = page_num
                            sections.append(current_section)
                        current_section = {
                            "heading": text,
                            "content": "",
                            "page_start": page_num,
                            "page_end": page_num
                        }

            page_text = "\n".join(page_text_blocks)
            if page_text.strip():
                is_scanned = False
                full_text_list.append(page_text)
                current_section["content"] += "\n" + page_text
            
            pages.append({
                "page_num": page_num,
                "text": page_text,
                "tables": tables
            })

        # Append last section
        if current_section["content"].strip():
            current_section["page_end"] = len(doc)
            sections.append(current_section)

        full_text = "\n\n".join(full_text_list)
        if len(full_text.strip()) < 100:
            is_scanned = True

        return {
            "full_text": full_text,
            "pages": pages,
            "sections": sections,
            "metadata": {
                "title": title,
                "page_count": len(doc),
                "file_size": file_size,
                "is_scanned": is_scanned
            },
            "extraction_method": "pymupdf"
        }

    def _parse_docx(self, filepath: str, file_size: int) -> Dict[str, Any]:
        try:
            doc = Document(filepath)
        except Exception as e:
            raise ValueError(f"Failed to open DOCX: {e}")

        pages = []
        sections = []
        full_text_list = []
        tables_md = []

        # Convert docx tables to markdown
        for table in doc.tables:
            markdown_rows = []
            for r_idx, row in enumerate(table.rows):
                row_cells = [cell.text.strip() for cell in row.cells]
                # Avoid exact duplicates if cells are merged
                row_cells_dedup = []
                for c in row_cells:
                    if not row_cells_dedup or row_cells_dedup[-1] != c:
                        row_cells_dedup.append(c)
                    else:
                        row_cells_dedup.append("")
                markdown_rows.append("| " + " | ".join(row_cells_dedup) + " |")
                if r_idx == 0:
                    markdown_rows.append("| " + " | ".join(["---"] * len(row_cells_dedup)) + " |")
            if markdown_rows:
                tables_md.append("\n".join(markdown_rows))

        current_section = {"heading": "Introduction", "content": "", "page_start": 1, "page_end": 1}
        page_text_accumulator = []
        current_page_num = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            full_text_list.append(text)
            page_text_accumulator.append(text)

            # Detect headings
            is_heading = para.style.name.startswith('Heading') or (
                len(text) < 120 and (
                    re.match(r'^(\d+\.\d*)\s+[A-Z]', text) or 
                    re.match(r'^(SECTION|CHAPTER)\s+[I|V|X|L|\d+]', text, re.IGNORECASE) or
                    text.isupper()
                )
            )

            if is_heading:
                if current_section["content"].strip():
                    current_section["page_end"] = current_page_num
                    sections.append(current_section)
                current_section = {
                    "heading": text,
                    "content": "",
                    "page_start": current_page_num,
                    "page_end": current_page_num
                }

            current_section["content"] += "\n" + text

            # Approximate pages based on character count (1800 chars per page)
            total_chars = sum(len(t) for t in page_text_accumulator)
            if total_chars > 1800:
                pages.append({
                    "page_num": current_page_num,
                    "text": "\n".join(page_text_accumulator),
                    "tables": tables_md if current_page_num == 1 else []  # Attach tables to first page
                })
                page_text_accumulator = []
                current_page_num += 1

        if page_text_accumulator or not pages:
            pages.append({
                "page_num": current_page_num,
                "text": "\n".join(page_text_accumulator),
                "tables": tables_md if not pages else []
            })

        if current_section["content"].strip():
            current_section["page_end"] = current_page_num
            sections.append(current_section)

        full_text = "\n\n".join(full_text_list)
        title = os.path.basename(filepath)

        return {
            "full_text": full_text,
            "pages": pages,
            "sections": sections,
            "metadata": {
                "title": title,
                "page_count": len(pages),
                "file_size": file_size,
                "is_scanned": False
            },
            "extraction_method": "python-docx"
        }
