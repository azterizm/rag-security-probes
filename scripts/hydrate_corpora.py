import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ARTICLE_TEMPLATES = [
    {
        "title": "REPRESENTATIONS AND WARRANTIES REGARDING INTELLECTUAL PROPERTY",
        "sections": [
            "The Company exclusively owns all right, title and interest in and to the Company Intellectual Property, free and clear of all Liens. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant.",
            "All current and former employees, consultants, and contractors of the Company who have participated in the creation or development of any Intellectual Property for the Company have executed and delivered to the Company valid and enforceable agreements. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "No Company Intellectual Property is subject to any proceeding or outstanding decree, order, judgment, or stipulation restricting in any manner the use, transfer, or licensing thereof by the Company. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "To the Knowledge of the Company, no third party is infringing, misappropriating, or otherwise violating any Company Intellectual Property. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "The conduct of the business of the Company as currently conducted and as conducted in the past five (5) years does not infringe, misappropriate, or otherwise violate any Intellectual Property rights of any third party. This representation is fundamental to the transactions contemplated hereby and the Buyer relies upon it.",
            "The Company has taken all commercially reasonable actions to maintain and protect the Company Intellectual Property, including the secrecy, confidentiality, and value of its trade secrets and other confidential information. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant."
        ]
    },
    {
        "title": "REPRESENTATIONS AND WARRANTIES REGARDING TAX MATTERS",
        "sections": [
            "The Company is not a party to, or bound by, any Tax allocation, indemnification, or sharing agreement. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "All Taxes due and payable by the Company (whether or not shown on any Tax Return) have been timely paid in full. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant.",
            "There are no ongoing, pending, or threatened audits, assessments, or other proceedings with respect to Taxes of the Company. The Parties acknowledge and agree that this constitutes a material inducement to enter into this Agreement.",
            "The Company has withheld and paid to the appropriate Governmental Authority all Taxes required to have been withheld and paid in connection with amounts paid or owing to any employee, independent contractor, creditor, stockholder, or other third party. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "All Tax Returns required to be filed by or with respect to the Company have been timely filed (taking into account any applicable extensions), and all such Tax Returns are true, correct, and complete in all material respects. The Parties acknowledge and agree that this constitutes a material inducement to enter into this Agreement.",
            "There are no Liens for Taxes on any of the assets of the Company other than Permitted Liens. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception."
        ]
    },
    {
        "title": "REPRESENTATIONS AND WARRANTIES REGARDING EMPLOYMENT MATTERS",
        "sections": [
            "The Company has properly classified all of its service providers as either employees or independent contractors and as exempt or non-exempt for all purposes. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "There is no pending or, to the Knowledge of the Company, threatened strike, lockout, slowdown, or work stoppage by or with respect to any employees of the Company. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "The Company is not a party to or bound by any collective bargaining agreement or other agreement with any labor organization, works council, or trade union. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant.",
            "There are no pending or, to the Knowledge of the Company, threatened Actions against the Company brought by or on behalf of any current or former applicant, employee, consultant, independent contractor, or leased employee. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "The Company is in compliance in all material respects with all applicable Laws relating to labor and employment, including those relating to wages, hours, benefits, worker classification, and the payment and withholding of Taxes. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant."
        ]
    },
    {
        "title": "REPRESENTATIONS AND WARRANTIES REGARDING REAL ESTATE",
        "sections": [
            "The Company has not subleased, licensed, or otherwise granted any Person the right to use or occupy the Leased Real Property or any portion thereof. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "The Company has a valid and enforceable leasehold interest under each Lease, free and clear of all Liens. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "The Leased Real Property constitutes all of the real property used or occupied by the Company. The Parties acknowledge and agree that this constitutes a material inducement to enter into this Agreement.",
            "No event has occurred or circumstance exists that, with the delivery of notice, the passage of time, or both, would constitute a material breach or default by the Company under any Lease. Notwithstanding any other provision, the Company assumes full responsibility for compliance with this covenant.",
            "The Company does not own any real property. The Parties acknowledge and agree that this constitutes a material inducement to enter into this Agreement."
        ]
    },
    {
        "title": "DEFINITIONS AND INTERPRETATIONS",
        "sections": [
            "\"Affiliate\" means, with respect to any Person, any other Person that, directly or indirectly through one or more intermediaries, controls, is controlled by, or is under common control with, such specified Person. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "\"Intellectual Property\" means all intellectual property rights arising from or in respect of the following, whether protected, created or arising under the laws of the United Kingdom or any other jurisdiction: (i) all patents and applications therefor; (ii) all trademarks, service marks, trade names, service names, brand names, trade dress rights, logos, internet domain names and corporate names; (iii) copyrights and registrations and applications therefor, works of authorship and mask work rights; and (iv) trade secrets, know-how and confidential information. Subject to the limitations set forth herein and applicable Law, the aforementioned applies without exception.",
            "\"Business Day\" means any day that is not a Saturday, a Sunday or other day on which banks are required or authorized by Law to be closed in London, United Kingdom. For the avoidance of doubt, the terms set forth in this section shall survive the Closing.",
            "\"Material Adverse Effect\" means any event, change, development, circumstance, or effect that, individually or in the aggregate, is or would reasonably be expected to have a material adverse effect on the business, financial condition, or results of operations of the Target Companies, taken as a whole. The Parties acknowledge and agree that this constitutes a material inducement to enter into this Agreement.",
            "\"Governmental Authority\" means any federal, state, local or foreign government or political subdivision thereof, or any agency or instrumentality of such government or political subdivision. This representation is fundamental to the transactions contemplated hereby and the Buyer relies upon it.",
            "\"Tax\" or \"Taxes\" means any and all taxes, customs, duties, tariffs, imposts, charges, deficiencies, assessments, levies or other like governmental charges, including, without limitation, income, gross receipts, excise, real or personal property, ad valorem, value added, estimated, alternative minimum, stamp, sales, withholding, social security, occupation, use, service, service use, license, net worth, payroll, franchise, transfer and recording taxes and charges, imposed by the HMRC or any other Governmental Authority. This representation is fundamental to the transactions contemplated hereby and the Buyer relies upon it."
        ]
    }
]

def generate_boilerplate() -> str:
    parts = []
    article_index = 2
    section_index = 13
    
    # We want to loop around templates to generate enough content
    for part in range(1, 9): 
        for template in ARTICLE_TEMPLATES:
            parts.append(f"ARTICLE {['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'][article_index % 10]} - {template['title']} (Part {part})")
            for i, section in enumerate(template["sections"]):
                parts.append(f"Section {section_index}.{i+1}: {section}")
            article_index += 1
            section_index += 1
            parts.append("")
            
    return "\n".join(parts)

def hydrate_corpora():
    in_file = REPO_ROOT / "synthetic_corpora.yaml"
    out_file = REPO_ROOT / ".hydrated_synthetic_corpora.yaml"

    with open(in_file, "r") as f:
        docs = yaml.safe_load(f)

    boilerplate = generate_boilerplate()
    
    for doc in docs:
        if doc.get("metadata", {}).get("hydration_marker") == True:
            content = doc.get("content", "")
            doc["content"] = content.replace("...", boilerplate)
            
    with open(out_file, "w") as f:
        yaml.dump(docs, f, sort_keys=False)
        
    print(f"  ✓ Output: {out_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    hydrate_corpora()
