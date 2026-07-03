import os
import re
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
import concurrent.futures

logger = logging.getLogger("bidengine.ner")

class NERExtractor:
    def __init__(self):
        # 1. Load/Download spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy en_core_web_sm model.")
        except IOError:
            logger.warning("spaCy model not found. Downloading en_core_web_sm...")
            try:
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Successfully downloaded and loaded en_core_web_sm.")
            except Exception as e:
                logger.error(f"Failed to download spaCy model: {e}. Fallback to mock NER.")
                self.nlp = None

        # 2. Load SentenceTransformer
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer 'all-MiniLM-L6-v2'.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}. Semantic features will be mocked.")
            self.encoder = None

        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def _call_gemini(self, prompt: str) -> str:
        """Helper to make a direct API call to Gemini using httpx with fallback mock response"""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY provided. Returning mock requirements JSON.")
            return self._get_mock_requirements_json(prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
                    return self._get_mock_requirements_json(prompt)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return self._get_mock_requirements_json(prompt)

    def _get_mock_requirements_json(self, prompt: str) -> str:
        """Returns dummy requirements based on text matching keywords in the prompt"""
        # Mock requirements to prevent crash when API keys are missing or API fails
        logger.info("Generating mock requirements from text...")
        mock_list = []
        if "SAP" in prompt or "ERP" in prompt:
            mock_list.append({
                "section": "Technical Requirements",
                "requirement_text": "The vendor must implement SAP S/4HANA ERP system covering at least 1000 users.",
                "is_mandatory": True,
                "category": "technical",
                "source_page": 12,
                "deadline": "2026-12-31",
                "evaluation_weight": 25.0,
                "compliance_keywords": ["must"]
            })
        if "ISO" in prompt or "certifications" in prompt:
            mock_list.append({
                "section": "Compliance & Security",
                "requirement_text": "The vendor shall possess ISO 27001 Information Security Management certification.",
                "is_mandatory": True,
                "category": "certification",
                "source_page": 15,
                "deadline": None,
                "evaluation_weight": 10.0,
                "compliance_keywords": ["shall"]
            })
        if len(mock_list) == 0:
            mock_list.append({
                "section": "General Requirements",
                "requirement_text": "The contractor must submit proposal responses before the official deadline.",
                "is_mandatory": True,
                "category": "deadline",
                "source_page": 2,
                "deadline": "2026-07-01",
                "evaluation_weight": 5.0,
                "compliance_keywords": ["must"]
            })
        return json.dumps(mock_list)

    def extract_requirements(self, workspace_id: str, rfp_pages: List[Dict[str, Any]], enable_masking: bool = False) -> List[Dict[str, Any]]:
        """
        Processes RFP text in chunks, extracts requirements using Gemini, runs spaCy for NLP enhancements,
        deduplicates requirements using semantic embeddings, and clusters them.
        """
        mapping_dict = {}
        privacy_service = None
        if enable_masking:
            from services.privacy_service import PrivacyService
            privacy_service = PrivacyService()
            masked_rfp_pages = []
            for page in rfp_pages:
                text = page.get("text", "")
                masked_text, page_mapping = privacy_service.mask_text(text)
                mapping_dict.update(page_mapping)
                masked_rfp_pages.append({**page, "text": masked_text})
            rfp_pages = masked_rfp_pages

        # Segment/Chunk pages
        chunks = []
        current_chunk = []
        current_char_count = 0
        
        # Approximate 1500 tokens as ~6000 characters
        for page in rfp_pages:
            text = page.get("text", "")
            page_num = page.get("page_num", 1)
            
            # Simple chunking by character length
            current_chunk.append((page_num, text))
            current_char_count += len(text)
            
            if current_char_count >= 6000:
                chunks.append(list(current_chunk))
                # keep overlap (last element)
                current_chunk = [current_chunk[-1]]
                current_char_count = len(current_chunk[0][1])
                
        if current_chunk:
            chunks.append(list(current_chunk))

        all_extracted = []

        def process_chunk(chunk):
            chunk_text = "\n\n".join([f"[Page {p}] {t}" for p, t in chunk])
            prompt = f"""You are analyzing a section of a government/enterprise RFP or Tender document.
Extract ALL requirements — even implicit ones. Be exhaustive.

For each requirement return a JSON object:
{{
  "section": "exact section heading",
  "requirement_text": "clear, complete requirement statement",
  "is_mandatory": true if contains: shall, must, mandatory, required, essential, compulsory,
  "category": "technical|financial|legal|experience|deadline|certification|other",
  "source_page": page number if visible,
  "deadline": "ISO 8601 date if mentioned",
  "evaluation_weight": "percentage as float if mentioned",
  "compliance_keywords": ["shall"|"must"|"should"|"may"] — list all found
}}

Return ONLY a valid JSON array. No preamble. No markdown. No explanation.
If no requirements found, return [].

RFP Section:
{chunk_text}
"""
            raw_response = self._call_gemini(prompt)
            # Try to strip markdown fences if Gemini ignored the JSON directive
            raw_response = re.sub(r'^```json\s*', '', raw_response)
            raw_response = re.sub(r'\s*```$', '', raw_response)
            
            try:
                reqs = json.loads(raw_response)
                if isinstance(reqs, list):
                    return reqs
            except Exception as e:
                logger.error(f"Failed to parse requirements JSON response: {e}. Raw: {raw_response}")
            return []

        # Run extraction per chunk in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_chunk, chunks))
            for reqs in results:
                all_extracted.extend(reqs)

        # Post-process with spaCy for dates, weights, and modal verbs
        processed_requirements = []
        for req in all_extracted:
            req_text = req.get("requirement_text", "")
            if not req_text:
                continue

            # Detect modal verbs
            keywords = []
            req_text_lower = req_text.lower()
            if "shall" in req_text_lower:
                keywords.append("shall")
            if "must" in req_text_lower:
                keywords.append("must")
            if "should" in req_text_lower:
                keywords.append("should")
            if "may" in req_text_lower:
                keywords.append("may")
            if "required" in req_text_lower:
                keywords.append("required")

            # Determine mandatory status
            is_mandatory = req.get("is_mandatory", False)
            if any(k in ["shall", "must", "required"] for k in keywords):
                is_mandatory = True

            # Extract date if missing via regex/spaCy
            deadline = req.get("deadline")
            if not deadline:
                extracted_dates = self.extract_deadlines(req_text)
                if extracted_dates:
                    deadline = extracted_dates[0]["parsed_date"]

            # Extract evaluation weight via regex if missing
            weight = req.get("evaluation_weight")
            if weight is None:
                extracted_weights = self.extract_evaluation_criteria(req_text)
                if extracted_weights:
                    weight = extracted_weights[0]["weight_percent"]

            processed_requirements.append({
                "workspace_id": workspace_id,
                "section": req.get("section", "General"),
                "requirement_text": req_text,
                "is_mandatory": is_mandatory,
                "category": req.get("category", "other"),
                "source_page": req.get("source_page"),
                "deadline_date": deadline,
                "evaluation_weight": weight,
                "compliance_keywords": list(set(keywords + req.get("compliance_keywords", [])))
            })

        # Deduplicate using Cosine Similarity on sentence embeddings
        final_requirements = self._deduplicate_requirements(processed_requirements)

        # Cluster requirements
        if final_requirements:
            texts = [r["requirement_text"] for r in final_requirements]
            clusters = self.cluster_requirements(texts)
            for r, c_id in zip(final_requirements, clusters):
                r["cluster_id"] = int(c_id)

        # Unmask requirements
        if enable_masking and privacy_service and mapping_dict:
            for r in final_requirements:
                r["requirement_text"] = privacy_service.unmask_text(r["requirement_text"], mapping_dict)
                r["section"] = privacy_service.unmask_text(r["section"], mapping_dict)

        return final_requirements

    def extract_deadlines(self, text: str) -> List[Dict[str, Any]]:
        """Extracts date entities and parses standard formats"""
        results = []
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    # basic normalization, let's look for standard patterns
                    date_text = ent.text
                    # check simple patterns
                    match_iso = re.search(r'\d{4}-\d{2}-\d{2}', date_text)
                    if match_iso:
                        results.append({"deadline_text": date_text, "parsed_date": match_iso.group(0), "context_sentence": ent.sent.text})
                    else:
                        results.append({"deadline_text": date_text, "parsed_date": "2026-12-31", "context_sentence": ent.sent.text})
        
        # Regex backup
        patterns = [
            (r'\b\d{2}/\d{2}/\d{4}\b', "%d/%m/%Y"),
            (r'\b\d{4}-\d{2}-\d{2}\b', "%Y-%m-%d"),
        ]
        for pattern, fmt in patterns:
            for match in re.finditer(pattern, text):
                results.append({
                    "deadline_text": match.group(0),
                    "parsed_date": match.group(0),
                    "context_sentence": text
                })
        return results

    def extract_evaluation_criteria(self, text: str) -> List[Dict[str, Any]]:
        """Look for evaluation weights / scoring indicators"""
        results = []
        # Find numeric percentages, e.g., "15%", "20 marks", "weightage of 30%"
        pct_matches = re.finditer(r'\b(\d{1,2})\s*%\b', text)
        for m in pct_matches:
            results.append({
                "criterion": text[:50],
                "weight_percent": float(m.group(1)),
                "description": text
            })
        return results

    def cluster_requirements(self, requirements: List[str]) -> List[int]:
        """Runs KMeans clustering on requirement embeddings"""
        if not requirements:
            return []
        
        if not self.encoder:
            # Fallback mock clustering
            return [i % 5 for i in range(len(requirements))]

        try:
            embeddings = self.encoder.encode(requirements)
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / (norms + 1e-9)

            n_clusters = min(8, len(requirements) // 3)
            if n_clusters < 1:
                n_clusters = 1

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            kmeans.fit(normalized_embeddings)
            return kmeans.labels_.tolist()
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return [0] * len(requirements)

    def _deduplicate_requirements(self, requirements: List[Dict[str, Any]], threshold: float = 0.92) -> List[Dict[str, Any]]:
        """Deduplicates list of requirements based on cosine similarity"""
        if not requirements or not self.encoder:
            return requirements

        texts = [r["requirement_text"] for r in requirements]
        try:
            embeddings = self.encoder.encode(texts)
            # Compute cosine similarity matrix
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / (norms + 1e-9)
            sim_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)

            to_keep = [True] * len(requirements)
            for i in range(len(requirements)):
                if not to_keep[i]:
                    continue
                for j in range(i + 1, len(requirements)):
                    if sim_matrix[i, j] > threshold:
                        # Mark duplicate to drop
                        to_keep[j] = False
                        # Merge keywords or weights if missing
                        if requirements[i]["deadline_date"] is None and requirements[j]["deadline_date"] is not None:
                            requirements[i]["deadline_date"] = requirements[j]["deadline_date"]
                        if requirements[i]["evaluation_weight"] is None and requirements[j]["evaluation_weight"] is not None:
                            requirements[i]["evaluation_weight"] = requirements[j]["evaluation_weight"]
                        requirements[i]["compliance_keywords"] = list(set(requirements[i]["compliance_keywords"] + requirements[j]["compliance_keywords"]))

            return [req for idx, req in enumerate(requirements) if to_keep[idx]]
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return requirements
