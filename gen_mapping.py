import re

markdown_table = """
| A One Steels India Limited | A One Steel India Limited |
| A V Thomas and Co Limited | A V Thomas & Co. Limited Unlisted Shares |
| Amol Minechem Limited | Amol Minechem Limited |
| Anheuser Busch Inbev (Sabmiller) India Ltd | Anheuser Busch Inbev (Sabmiller) India Limited Unlisted Shares |
| Anugraha Valve Castings Limited | Anugraha Valve Castings Limited Unlisted Shares |
| API Holdings Ltd - Pharmeasy | PharmEasy Unlisted Shares |
| Apollo Green Energy Ltd | Apollo Green Energy Limited Unlisted Shares |
| Arohan Financial Services | Arohan Financial Services Unlisted Shares |
| ASK Investment Managers Limited | ASK Investment Managers Limited |
| Assam Carbon Products Limited | Assam Carbon Products Limited Unlisted Shares |
| Axles India Limited | Axles India Limited Unlisted Shares |
| B9 Beverages Limited - Bira | Bira Unlisted Shares |
| Berar Finance Limited | Berar Finance Limited |
| Bharat Nidhi Limited | Bharat Nidhi (Bharat Bank) Unlisted Shares |
| Big Basket | Big Basket Unlisted Shares |
| boAt - Imagine Marketing Limited | Boat Unlisted Share (Imagine Marketing) |
| Bootes Impex Tech Ltd. | Bootes Impex Tech Ltd. |
| Capgemini Technology Services India Limited | Capgemini Technology Services India Limited Unlisted Shares |
| Care Health Insurance Ltd | Care Health (Previously Religare Health) Insurance Company Limited Unlisted Shares |
| Carrier Airconditioning and Refrigeration Limited | Carrier Airconditioning & Refrigeration Limited Unlisted Shares |
| Cheelizza Pizza India Limited | Cheelizza Pizza Unlisted Shares |
| Chennai Super Kings Cricket Limited - CSK | CSK Unlisted Shares |
| Cochin International Airport Limited | Cochin International Airport Limited Unlisted Shares |
| Downtown Hospital Ltd | Down Town Hospital Limited Unlisted Shares |
| Ecosure Pulpmolding Technologies Limited | Ecosure Unlisted Shares |
| Electrosteel Steel Ltd - ESL Steel | Electrosteel Steels Limited Unlisted Shares |
| Empire Spices and Foods Limited | Empire Spices and Foods Limited Unlisted Shares |
| ESDS Software Solution Ltd | ESDS Unlisted Shares |
| Fincare Small Finance Bank Limited | Fincare Small Finance Bank Unlisted Shares |
| Fino Paytech Ltd. | Fino Paytech Limited Unlisted Shares |
| Fusion Techstack Limited | Fusion Techstack Limited (Formerly known as Indian Commodity Exchange Limited) |
| Gamma Rotors Limited | Gamma Rotors Limited |
| Garuda Aerospace Limited | Garuda Aerospace Limited |
| GFCL EV Products Limited | GFCL EV Products Limited |
| GKN Driveline India Limited | GKN Driveline India Limited Unlisted Shares |
| Goa Shipyard Limited | Goa Shipyard Limited Unlisted Shares |
| Goodluck Defence And Aerospace Ltd | Goodluck Defence And Aerospace Unlisted Shares |
| Goodluck Green Energy Ltd | Goodluck Green Energy Limited |
| Greenzo Energy India Limited | Greenzo Energy India Limited Unlisted Shares |
| HCIN Network Pvt Ltd | HCIN Networks Private Limited |
| HDFC Securities Limited | HDFC Securities Limited Unlisted Shares |
| Hella Infra Market Private Limited | Hella Infra Market Private Limited |
| Hero Fincorp Limited | Hero Fincorp Limited Unlisted Shares |
| Hero Motors Limited | Hero motors Limited |
| Hindon Mercantile Limited | Hindon Mercantile Limited |
| Hinduja Leyland Finance Limited | Hinduja Leyland Finance Limited |
| Hindustan Power Exchange Limited - HPX | Hindustan Power Exchange Limited (HPX India) |
| Honeywell Electrical Devices and Systems India Limited | Honeywell Electrical Devices and Systems India Unlisted Shares |
| ICL Fincorp Limited | ICL Fincorp Limited Unlisted Shares |
| IKF Finance | IKF Finance Limited Unlisted Shares |
| Incred Holdings Limited | Incred Holdings Limited Unlisted Shares |
| India Carbon Limited | India Carbon Limited Unlisted Shares |
| Indian Potash Ltd | Indian Potash Limited Unlisted Share |
| Indofil Industries Ltd | Indofil Industries Limited Unlisted Shares |
| Inkel Limited | Inkel Limited Unlisted Shares |
| Innov8 Workspaces India Limited | Innov8 Workspaces India Limited |
| Inox Clean Energy Limited | Inox Clean Energy Limited |
| Inox Leasing and Finance Limited | Inox Leasing and Finance Limited Unlisted Shares |
| Inox Renewable Solutions Limited | Inox Renewable Solutions Limited |
| Insolare Energy Limited | Insolare Energy Unlisted Shares |
| Jupiter International Limited | Jupiter International Limited |
| Kanara Consumer Products Limited | Kanara Consumer Products ( Formerly Known As Kurl-on Limited) Unlisted Shares |
| Kannur International Airport Limited | Kannur International Airport Limited Unlisted Shares |
| Kineco Limited | Kineco Limited Unlisted Share |
| KLM Axiva Finvest Limited | KLM Axiva Finvest Unlisted Shares Price |
| Kurlon Enterprise | KURLON Enterprise Limited Unlisted Shares |
| Lakeshore Hospital and Research Centre Limited | Lakeshore Hospital Unlisted Share Price |
| LAVA International Limited | LAVA International Limited Unlisted Shares |
| Lords Mark Industries | Lords Mark Industries Limited |
| Machint Solutions Limited | Machint Solutions Limited |
| Madbow Ventures Limited | Madbow Ventures Unlisted Shares |
| Maharashtra Knowledge Corporation Ltd - MKCL | Maharashtra Knowledge Corporation (MKCL) Limited Unlisted Shares |
| Manipal Payment and Identify Solutions Ltd | Manipal Payment & Identity Solutions Ltd (Manipal Cards) |
| Manjushree Technopack India Limited | Manjushree Technopack India Limited Unlisted Shares |
| Market Simplified India Ltd | Market Simplified Unlisted Shares Price |
| Martin and Harris Laboratories Limited | Martin and Harris Laboratories Limited Unlisted Shares |
| Matrix Gas and Renewables Limited | Matrix Gas And Renewables Unlisted Shares |
| Maverick Simulation Solutions Limited | Maverick Simulation Solutions Limited |
| Maxvalue Credits And Investments Ltd | Maxvalue Credits and Investments Unlisted Shares |
| Mayasheel Retail India Limited - Bazar India | Bazar India Unlisted Shares |
| Merino Industries Limited | Merino Industries Limited Unlisted Shares |
| Metropolitan Stock Exchange of India Limited - MSEI | Metropolitan Stock Exchange (MSEI) Unlisted Shares |
| Mohan Meakin Limited | Mohan Meakin Limited Unlisted Shares |
| Motilal Oswal Home Finance Limited | Motilal Oswal Home Finance Limited Unlisted Shares |
| Nayara Energy Ltd | Nayara Energy (Formerly Essar Oil) Limited Unlisted Shares |
| NCDEX (National Commodity and Derivatives Exchange) Limited | National Commodity & Derivatives Exchange (NCDEX) Limited Unlisted Shares |
| NCL Buildtek Limited | NCL Buildtek Limited (Previously NCL Alltek & Seccolor Limited) Unlisted Shares |
| NCL Holdings | NCL Holdings Unlisted Shares |
| NSE - National Stock Exchange | NSE India Limited Unlisted Shares |
| Onix Renewable Limited | Onix Renewable Limited |
| Oravel Stays Limited - OYO | ORAVEL STAYS LIMITED (Oyo Unlisted Shares) |
| Orbis Financial Corporation Ltd | ORBIS FINANCIAL CORPORATION Unlisted Shares |
| Otis Elevator Co (India) Limited | Otis Elevator (India) Limited Unlisted Shares |
| Philips Domestic Appliances India Limited | Philips Domestic Appliances India Unlisted Shares |
| Philips India Limited | Philips India Limited Unlisted Shares |
| Polymatech Electronics Pvt Ltd | Polymatech Unlisted Shares |
| Power Exchange India Limited - PXIL | Power Exchange India Limited (PXIL) |
| PPFAS - Parag Parikh Financial Advisory Services | Parag Parikh Financial Advisory Services Ltd. (PPFAS) |
| Quality Enviro Engineers Private Limited | Quality Enviro Engineers Private Limited |
| Resins and Plastics Limited | Resin & Plastic Limited Unlisted Shares |
| Ring Plus Aqua Limited | Ring Plus Aqua Limited Unlisted Shares |
| RoyalCare Super Speciality Hospital Limited | Royalcare Super Speciality Hospitals |
| RRP S4E Innovation Private Limited | RRP S4E innovation Unlisted Shares Price |
| S3V Vascular Technologies Limited | S3V Vascular Technologies Limited |
| SBI General Insurance Company Limited | SBI General Insurance Unlisted Shares |
| SBI Mutual Fund | SBI Mutual Fund Unlisted Shares |
| Shivchem Agro Limited | Shivchem Agro Limited |
| Shriram Life Insurance Company Limited | Shriram Life Insurance Co. Ltd Unlisted Shares |
| Signify Innovations India Limited | Signify Innovations (Previously Phillips Lighting) India Limited Unlisted Shares |
| Skyways Air Services Limited | Skyways Air Services Limited |
| Solar91 Cleantech Limited IPO | Solar 91 Cleantech Limited |
| Spray Engineering Devices Limited | Spray Engineering Devices Unlisted Shares |
| Sterlite Electric Limited | Sterlite Electric Limited (formerly Sterlite Power) Unlisted Shares |
| Sunday Proptech Limited - OYO Assets | Sunday Proptech Limited |
| The Ramaraju Surgical Cotton Mills Ltd | Ramaraju Surgical Cotton Mills Limited Unlisted Shares |
| Ticker Limited | Ticker Limited |
| Transline Technologies Limited | Transline Technologies Limited |
| Urban Tots - Deepak Houseware and Toys Pvt Ltd | Urban Tots Unlisted Shares |
| Utkarsh Micro Finance Ltd - Utkarsh CoreInvest Ltd | Utkarsh Micro Finance(Core Invest) Unlisted Shares |
| Veeda Clinical Research Limited (CRO) | Veeda Clinical Research Limited |
| Xtranet Technologies Private Limited | XtraNet Technologies Pvt. Ltd. |
| Zak Venture Ltd | Zak Venture Ltd |
| Zepto Limited | Zepto Unlisted Shares (Equity) *and* Zepto unlisted( CCPS shares((792.6461 Equity) |
"""

lines = markdown_table.strip().split('\n')
mapping = {}
for line in lines:
    if line.startswith('|'):
        parts = line.split('|')
        if len(parts) >= 3:
            sc_name = parts[1].strip()
            uz_name = parts[2].strip()
            if sc_name and uz_name:
                mapping[sc_name] = uz_name

with open('scraper/mapping.py', 'w', encoding='utf-8') as f:
    f.write('SHARESCART_TO_UNLISTEDZONE = {\n')
    for sc, uz in mapping.items():
        # Escape single quotes
        sc = sc.replace("'", "\\'")
        uz = uz.replace("'", "\\'")
        f.write(f"    '{sc}': '{uz}',\n")
    f.write('}\n')
