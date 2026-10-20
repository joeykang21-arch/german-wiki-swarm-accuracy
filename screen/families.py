"""Family assignment by page name (coordination pages only; test/sandbox/probe/scratch pages skipped)."""
import re
FAM = [("oecd-equity", r"OECD.*Equity|OECDEducationEquity|Equity.*OECD|TooltipEvidence|PrecisionScout"),
       ("oecd-rrp-co2", r"RegionalRecovery|^RRP"), ("oecd-hdi", r"HouseholdDisposable"),
       ("cashier-masters", r"CashiersMasters"), ("cashier-bachelors", r"Cashier"), ("cvd", r"CVD"),
       ("ihme-family-planning", r"FamilyPlanning"), ("sector", r"Sector"), ("grocery", r"Grocery"),
       ("construction-wage", r"ConstructionWage"), ("construction", r"Construction"),
       ("french", r"Language|LangR|French"), ("clothing", r"Clothing"), ("finance", r"Finance"),
       ("maids-wage", r"MaidsWage"), ("maids", r"Maids"), ("police", r"Police"),
       ("poverty-county", r"PovertyCounty"), ("fuel-poverty", r"FuelPoverty"), ("poverty", r"Poverty"),
       ("transport", r"Transport"), ("nyc-veterans", r"Veteran"), ("uefa", r"UEFA"),
       ("school-psych", r"SchoolPsych"), ("ivy-tuition", r"IvyTuition"), ("occupation-salary", r"OccupationSalary"),
       ("production-occupation", r"ProductionOccupation"), ("sdg", r"SDG"), ("healthdata-other", r"Healthdata(Smoking|MCV)"),
       ("dataafrica", r"DataAfrica"), ("lf", r"^LF"), ("state-sequence", r"DataUSAStateSequence")]
SKIP = re.compile(r"Test|Sandbox|Probe|Scratch", re.I)


def family(page):
    p = re.sub(r"^[a-z]+~", "", page)
    if SKIP.search(p):
        return None
    return next((f for f, r in FAM if re.search(r, p, re.I)), None)
