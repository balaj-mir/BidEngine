import re
import spacy
import logging
from typing import Tuple, Dict

logger = logging.getLogger("bidengine.privacy")

class PrivacyService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy loaded successfully in PrivacyService.")
        except Exception:
            self.nlp = None
            logger.warning("SpaCy en_core_web_sm not loaded in PrivacyService. Falling back to regex masking.")

    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Masks PII and sensitive data in text. Returns (masked_text, mapping).
        """
        if not text:
            return "", {}

        mapping = {}
        counter = {"EMAIL": 1, "PHONE": 1, "BUDGET": 1, "COMPANY": 1, "PERSON": 1}

        # 1. Mask Emails
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_pattern, text)
        for email in set(emails):
            placeholder = f"[EMAIL_{counter['EMAIL']}]"
            text = text.replace(email, placeholder)
            mapping[placeholder] = email
            counter["EMAIL"] += 1

        # 2. Mask Phone Numbers
        phone_pattern = r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        phones = [p for p in re.findall(phone_pattern, text) if len(re.sub(r'\D', '', p)) >= 7]
        for phone in set(phones):
            placeholder = f"[PHONE_{counter['PHONE']}]"
            text = text.replace(phone, placeholder)
            mapping[placeholder] = phone
            counter["PHONE"] += 1

        # 3. Mask Budgets / Currency
        budget_pattern = r'\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|M|B))?'
        budgets = re.findall(budget_pattern, text, re.IGNORECASE)
        for budget in set(budgets):
            placeholder = f"[BUDGET_{counter['BUDGET']}]"
            text = text.replace(budget, placeholder)
            mapping[placeholder] = budget
            counter["BUDGET"] += 1

        # 4. SpaCy NER Masking (ORG, PERSON)
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PERSON"):
                        val = ent.text.strip()
                        # Avoid masking placeholder tokens
                        if val.startswith("[") and val.endswith("]"):
                            continue
                        if len(val) < 3:
                            continue
                        label = "COMPANY" if ent.label_ == "ORG" else "PERSON"
                        placeholder = f"[{label}_{counter[label]}]"
                        if val not in mapping.values():
                            text = text.replace(val, placeholder)
                            mapping[placeholder] = val
                            counter[label] += 1
            except Exception as e:
                logger.error(f"SpaCy masking error: {e}")

        return text, mapping

    def unmask_text(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Restores original values for all placeholders in the text.
        """
        if not text or not mapping:
            return text

        for placeholder, original in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(placeholder, original)
        return text
