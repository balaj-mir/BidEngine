import os
import json
import random
from datetime import datetime, timedelta

def generate_datasets():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    # 1. Generate Capability Library (50 Records)
    capabilities = []
    
    # IT Services (20 Records)
    it_topics = [
        ("Cloud Migration", "Azure", "IT Services"),
        ("SAP ERP Implementation", "SAP S/4HANA", "IT Services"),
        ("Cybersecurity Operations Center", "SOC", "IT Services"),
        ("Mobile App Development", "Flutter", "IT Services"),
        ("Data Analytics Platform", "PowerBI", "IT Services"),
        ("IT Service Desk Support", "ITIL", "IT Services"),
        ("Network Infrastructure Upgrade", "Cisco", "IT Services"),
        ("Disaster Recovery Plan Setup", "DRP", "IT Services"),
        ("AI Chatbot Deployment", "NLP", "IT Services"),
        ("Blockchain Smart Contracts", "Solidity", "IT Services")
    ]
    
    for i in range(1, 21):
        topic, keyword, sector = it_topics[(i-1) % len(it_topics)]
        certifications = ["ISO 27001", "CMMI Level 3"]
        if "SAP" in topic:
            certifications.append("SAP Gold Partner")
        elif "Azure" in topic or "Cloud" in topic:
            certifications.append("Microsoft Gold Partner")
            
        cap = {
            "id": f"cap_{i:03d}",
            "title": f"{topic} for {random.choice(['FBR', 'NADRA', 'HBL', 'PTCL', 'NBP'])}",
            "description": f"Designed and deployed a state-of-the-art {topic} system. Covered over {random.choice([500, 1000, 2500])} active users. Delivered on time and within budget of PKR {random.randint(50, 250)}M.",
            "sector": sector,
            "client_type": random.choice(["Government", "Enterprise", "Financial"]),
            "year_completed": random.choice([2021, 2022, 2023, 2024, 2025]),
            "contract_value": float(random.randint(50000000, 300000000)),
            "currency": "PKR",
            "duration_months": random.choice([6, 12, 18, 24]),
            "certifications": certifications,
            "team_size": random.randint(15, 60),
            "keywords": [keyword.lower(), "digital transformation", "system integration", sector.lower()],
            "outcome": f"Achieved {random.choice([99.9, 99.7, 98.5])}% service uptime and {random.choice([25, 30, 45])}% operations cost reduction.",
            "client_reference_available": random.choice([True, False])
        }
        capabilities.append(cap)

    # Construction (10 Records)
    const_topics = [
        ("Highway Asphalt Paving", "Asphalt", "Construction"),
        ("Bridge Structural Reinforcement", "Concrete", "Construction"),
        ("Airport Runway Expansion", "Civil", "Construction"),
        ("Commercial High-Rise Development", "HVAC", "Construction"),
        ("Water Treatment Facility Construction", "Filter", "Construction")
    ]
    for i in range(21, 31):
        topic, keyword, sector = const_topics[(i-21) % len(const_topics)]
        cap = {
            "id": f"cap_{i:03d}",
            "title": f"{topic} at {random.choice(['Lahore Bypass', 'CPEC Section 4', 'Karachi Port', 'Gwadar Airport'])}",
            "description": f"Managed civil engineering works and materials supply for the {topic} development contract. Passed all third-party compaction and load-bearing audits.",
            "sector": sector,
            "client_type": "Government",
            "year_completed": random.choice([2020, 2021, 2022, 2023, 2024]),
            "contract_value": float(random.randint(150000000, 800000000)),
            "currency": "PKR",
            "duration_months": random.choice([12, 24, 36]),
            "certifications": ["ISO 9001", "PEC C1 Category"],
            "team_size": random.randint(50, 150),
            "keywords": [keyword.lower(), "infrastructure", "civil engineering", "construction"],
            "outcome": "Project delivered 2 months ahead of schedule with zero safety incidents logged.",
            "client_reference_available": True
        }
        capabilities.append(cap)

    # Logistics (10 Records)
    log_topics = [
        ("Fleet Tracking System Integration", "Fleet", "Logistics"),
        ("Cold-Chain Warehouse Establishment", "RFID", "Logistics"),
        ("Nationwide Supply Chain Distribution", "SLA", "Logistics"),
        ("Customs Clearing Automation Portal", "Customs", "Logistics"),
        ("Port Terminal Operations Management", "Container", "Logistics")
    ]
    for i in range(31, 41):
        topic, keyword, sector = log_topics[(i-31) % len(log_topics)]
        cap = {
            "id": f"cap_{i:03d}",
            "title": f"{topic} for {random.choice(['DHL Pakistan', 'National Logistics Cell (NLC)', 'PNSC'])}",
            "description": f"End-to-end management of warehouse storage and transport networks to optimize delivery routing and fuel efficiency.",
            "sector": sector,
            "client_type": random.choice(["Enterprise", "Government"]),
            "year_completed": random.choice([2021, 2022, 2023, 2024]),
            "contract_value": float(random.randint(40000000, 200000000)),
            "currency": "PKR",
            "duration_months": random.choice([8, 12, 18]),
            "certifications": ["ISO 9001", "IATA Cargo Certification"],
            "team_size": random.randint(20, 80),
            "keywords": [keyword.lower(), "supply chain", "distribution", "transportation"],
            "outcome": f"Reduced dispatch processing delays by {random.choice([15, 22, 30])}% with 99.8% shipping integrity.",
            "client_reference_available": random.choice([True, False])
        }
        capabilities.append(cap)

    # Consulting (10 Records)
    cons_topics = [
        ("Corporate Restructuring Advisory", "Advisory", "Consulting"),
        ("Enterprise Risk Audit", "Compliance", "Consulting"),
        ("Digital Marketing Strategy", "Growth", "Consulting"),
        ("Financial Feasibility Studies", "Audit", "Consulting"),
        ("Human Capital Training Program", "HR", "Consulting")
    ]
    for i in range(41, 51):
        topic, keyword, sector = cons_topics[(i-41) % len(cons_topics)]
        cap = {
            "id": f"cap_{i:03d}",
            "title": f"{topic} Advisory to {random.choice(['Ministry of Finance', 'Lucky Cement', 'Engro Corp'])}",
            "description": f"Led organizational diagnostic and executive training programs to design standard operating policies and strategic growth blueprints.",
            "sector": sector,
            "client_type": random.choice(["Enterprise", "Government", "Financial"]),
            "year_completed": random.choice([2022, 2023, 2024, 2025]),
            "contract_value": float(random.randint(10000000, 50000000)),
            "currency": "PKR",
            "duration_months": random.choice([3, 6, 9, 12]),
            "certifications": ["PMP", "Certified Management Consultant"],
            "team_size": random.randint(5, 15),
            "keywords": [keyword.lower(), "advisory", "strategy", "consulting"],
            "outcome": "Helped unlock 20% headcount efficiency and standardized 45 critical operational policies.",
            "client_reference_available": True
        }
        capabilities.append(cap)

    with open(os.path.join(data_dir, "capability_library.json"), "w") as f:
        json.dump(capabilities, f, indent=2)

    # 2. Generate Bid History (120 Bids: 65 WON, 55 LOST)
    bid_history = []
    
    # 65 WON bids
    for i in range(1, 66):
        comp = random.randint(78, 100)
        exp = random.randint(75, 100)
        budget = random.uniform(0.70, 0.95)
        quality = random.randint(75, 98)
        competitors = random.randint(1, 3)
        timeline = random.randint(15, 60)
        
        bid = {
            "id": f"bid_w_{i:03d}",
            "rfp_title": f"Tender for {random.choice(['ERP System Upgrade', 'Cloud Migration Phase 2', 'Bypass Road Construction', 'Supply Chain Advisory'])}",
            "sector": random.choice(["IT Services", "Construction", "Logistics", "Consulting"]),
            "client_type": random.choice(["Government", "Enterprise", "Financial"]),
            "outcome": "WON",
            "contract_value": float(random.randint(40000000, 400000000)),
            "currency": "PKR",
            "bid_submitted_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "evaluation_score_received": float(random.randint(80, 96)),
            "compliance_score": comp,
            "domain_experience_score": exp,
            "budget_alignment": float(round(budget, 2)),
            "submission_quality_score": quality,
            "past_relationship_with_client": random.choice([True, True, False]), # High relationship probability
            "incumbent_present": random.choice([False, False, True]), # Low incumbent probability
            "bid_cost_estimate": random.randint(100000, 300000),
            "competitor_count": competitors,
            "timeline_days": timeline,
            "certifications_required": True,
            "certifications_met": True
        }
        bid_history.append(bid)

    # 55 LOST bids
    for i in range(1, 56):
        comp = random.randint(30, 77) # Low compliance
        exp = random.randint(25, 74)  # Low experience
        budget = random.uniform(0.30, 0.69) # Poor price fit
        quality = random.randint(40, 74)
        competitors = random.randint(3, 8)  # High competition
        timeline = random.randint(45, 90)
        
        bid = {
            "id": f"bid_l_{i:03d}",
            "rfp_title": f"Sollicitation for {random.choice(['IT Infrastructure Support', 'Highway Overpass Bridge', 'Fleet Tracking Solutions', 'Digital Advisory Audits'])}",
            "sector": random.choice(["IT Services", "Construction", "Logistics", "Consulting"]),
            "client_type": random.choice(["Government", "Enterprise", "Financial"]),
            "outcome": "LOST",
            "contract_value": float(random.randint(80000000, 600000000)),
            "currency": "PKR",
            "bid_submitted_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "evaluation_score_received": float(random.randint(45, 75)),
            "compliance_score": comp,
            "domain_experience_score": exp,
            "budget_alignment": float(round(budget, 2)),
            "submission_quality_score": quality,
            "past_relationship_with_client": random.choice([False, False, True]), # Low relationship
            "incumbent_present": random.choice([True, True, False]), # High incumbent risk
            "bid_cost_estimate": random.randint(150000, 450000),
            "competitor_count": competitors,
            "timeline_days": timeline,
            "certifications_required": True,
            "certifications_met": random.choice([False, True, False]) # Sometimes certification failed
        }
        bid_history.append(bid)

    # Shuffle history
    random.shuffle(bid_history)

    with open(os.path.join(data_dir, "bid_history.json"), "w") as f:
        json.dump(bid_history, f, indent=2)

    print("Successfully generated capability_library.json and bid_history.json seed datasets!")

if __name__ == "__main__":
    generate_datasets()
