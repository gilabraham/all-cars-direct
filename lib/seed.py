"""Sample listing data + helpers to seed the DB and export CSV templates."""
from __future__ import annotations

import io

import pandas as pd

from . import db

# Single source of truth for sample inventory.
# (make, model, year, trim, body, deal_type, fuel, monthly, down, term,
#  miles, msrp, selling, mf, residual%, color, location, dealer, featured)
_ROWS = [
    ("Toyota", "RAV4", 2025, "XLE Premium", "SUV", "Lease", "Gas", 329, 1995, 36, 12000, 35420, 34100, 0.00150, 62, "Lunar Rock", "Los Angeles, CA", "Toyota of Downtown LA", 1),
    ("Honda", "Civic", 2025, "Sport Touring", "Sedan", "Lease", "Gas", 289, 1500, 36, 12000, 31250, 30100, 0.00120, 60, "Rallye Red", "San Jose, CA", "Capitol Honda", 0),
    ("Honda", "CR-V", 2025, "EX-L", "SUV", "Lease", "Gas", 349, 2200, 36, 10000, 36800, 35400, 0.00140, 61, "Meteorite Gray", "Seattle, WA", "Pacific Honda", 0),
    ("Tesla", "Model 3", 2026, "Long Range AWD", "Sedan", "Lease", "Electric", 399, 2999, 36, 10000, 47990, 46500, 0.00090, 55, "Stealth Grey", "Fremont, CA", "Tesla Fremont", 1),
    ("Tesla", "Model Y", 2026, "Long Range", "SUV", "Finance", "Electric", 629, 5000, 72, None, 50990, 49200, None, None, "Pearl White", "Austin, TX", "Tesla Austin", 1),
    ("BMW", "330i", 2025, "xDrive", "Sedan", "Lease", "Gas", 519, 3500, 36, 10000, 49200, 47100, 0.00160, 58, "Alpine White", "Miami, FL", "BMW of Miami", 0),
    ("BMW", "X5", 2025, "xDrive40i", "SUV", "Lease", "Gas", 829, 5500, 36, 10000, 73900, 70800, 0.00180, 60, "Black Sapphire", "Dallas, TX", "BMW of Dallas", 1),
    ("Mercedes-Benz", "C300", 2025, "4MATIC", "Sedan", "Lease", "Gas", 599, 3995, 36, 10000, 52400, 50100, 0.00175, 57, "Selenite Grey", "New York, NY", "MB Manhattan", 0),
    ("Mercedes-Benz", "GLC 300", 2025, "4MATIC", "SUV", "Lease", "Gas", 689, 4500, 36, 10000, 58900, 56200, 0.00185, 59, "Polar White", "Chicago, IL", "MB of Chicago", 0),
    ("Audi", "Q5", 2025, "Premium Plus", "SUV", "Lease", "Gas", 629, 3999, 36, 10000, 56300, 53800, 0.00170, 58, "Glacier White", "Denver, CO", "Audi Denver", 0),
    ("Audi", "A4", 2025, "Premium", "Sedan", "Lease", "Gas", 499, 3500, 36, 10000, 45800, 43900, 0.00155, 57, "Mythos Black", "Phoenix, AZ", "Audi North Scottsdale", 0),
    ("Hyundai", "Tucson", 2025, "SEL Convenience", "SUV", "Lease", "Gas", 279, 2495, 36, 12000, 33150, 31900, 0.00110, 60, "Amazon Gray", "Atlanta, GA", "Hyundai of Atlanta", 0),
    ("Hyundai", "IONIQ 5", 2026, "SEL AWD", "Crossover", "Lease", "Electric", 319, 3999, 24, 10000, 49700, 47800, 0.00050, 60, "Cyber Gray", "Portland, OR", "Hyundai Portland", 1),
    ("Kia", "Telluride", 2025, "EX", "SUV", "Finance", "Gas", 689, 3000, 72, None, 43990, 42500, None, None, "Ebony Black", "Houston, TX", "Kia of Houston", 0),
    ("Kia", "EV6", 2026, "Wind AWD", "Crossover", "Lease", "Electric", 339, 3999, 24, 10000, 51200, 49100, 0.00060, 59, "Runway Red", "San Diego, CA", "Kia San Diego", 0),
    ("Ford", "F-150", 2025, "XLT SuperCrew", "Truck", "Finance", "Gas", 749, 4000, 72, None, 58600, 55900, None, None, "Oxford White", "Detroit, MI", "Ford of Detroit", 1),
    ("Ford", "Mustang Mach-E", 2026, "Premium AWD", "SUV", "Lease", "Electric", 429, 3500, 36, 10000, 52400, 49900, 0.00100, 56, "Grabber Blue", "Boston, MA", "Boston Ford", 0),
    ("Chevrolet", "Silverado 1500", 2025, "LT", "Truck", "Finance", "Gas", 699, 4500, 72, None, 54900, 52100, None, None, "Summit White", "Nashville, TN", "Chevy Nashville", 0),
    ("Chevrolet", "Equinox EV", 2026, "LT AWD", "SUV", "Lease", "Electric", 309, 2999, 24, 10000, 41900, 40100, 0.00070, 58, "Riptide Blue", "Charlotte, NC", "Chevy Charlotte", 0),
    ("Subaru", "Outback", 2025, "Premium", "Wagon", "Lease", "Gas", 319, 2495, 36, 12000, 34200, 33000, 0.00130, 62, "Autumn Green", "Salt Lake City, UT", "Subaru SLC", 0),
    ("Subaru", "Crosstrek", 2025, "Sport", "Crossover", "Lease", "Gas", 289, 1995, 36, 12000, 30600, 29500, 0.00120, 63, "Sun Blaze Pearl", "Minneapolis, MN", "Subaru of MN", 0),
    ("Mazda", "CX-5", 2025, "Carbon Turbo", "SUV", "Lease", "Gas", 339, 2495, 36, 12000, 36400, 34900, 0.00140, 60, "Soul Red", "Tampa, FL", "Mazda Tampa", 0),
    ("Mazda", "Mazda3", 2025, "Premium", "Hatchback", "Lease", "Gas", 299, 1995, 36, 12000, 31500, 30200, 0.00130, 59, "Machine Gray", "Sacramento, CA", "Mazda Sacramento", 0),
    ("Lexus", "RX 350", 2025, "Premium", "SUV", "Lease", "Gas", 619, 3999, 36, 10000, 54800, 52600, 0.00150, 59, "Nori Green", "San Francisco, CA", "Lexus SF", 1),
    ("Lexus", "ES 350", 2025, "F Sport", "Sedan", "Lease", "Gas", 519, 3500, 36, 10000, 49100, 47000, 0.00140, 57, "Ultra White", "Las Vegas, NV", "Lexus of Las Vegas", 0),
    ("Volkswagen", "Tiguan", 2025, "SE", "SUV", "Lease", "Gas", 299, 2495, 36, 12000, 33800, 32400, 0.00125, 58, "Pure White", "Columbus, OH", "VW Columbus", 0),
    ("Volkswagen", "ID.4", 2026, "Pro S", "SUV", "Lease", "Electric", 279, 2999, 24, 10000, 45300, 43200, 0.00060, 57, "Aurora Red", "Philadelphia, PA", "VW Philadelphia", 0),
    ("Jeep", "Grand Cherokee", 2025, "Limited", "SUV", "Lease", "Gas", 569, 3995, 36, 10000, 51200, 48900, 0.00170, 56, "Diamond Black", "Kansas City, MO", "Jeep KC", 0),
    ("Jeep", "Wrangler", 2025, "Sahara 4xe", "SUV", "Lease", "Plug-in Hybrid", 499, 3500, 36, 10000, 54600, 52300, 0.00160, 58, "Firecracker Red", "Denver, CO", "Jeep Denver", 0),
    ("Nissan", "Rogue", 2025, "SV", "SUV", "Lease", "Gas", 289, 2495, 36, 12000, 32700, 31300, 0.00130, 59, "Gun Metallic", "Orlando, FL", "Nissan Orlando", 0),
    ("Nissan", "Ariya", 2026, "Engage", "Crossover", "Lease", "Electric", 269, 2999, 24, 10000, 44900, 42800, 0.00055, 56, "Boulder Gray", "Raleigh, NC", "Nissan Raleigh", 0),
    ("Acura", "MDX", 2025, "Technology", "SUV", "Lease", "Gas", 659, 4500, 36, 10000, 58300, 55700, 0.00150, 58, "Liquid Carbon", "St. Louis, MO", "Acura St. Louis", 0),
    ("Acura", "Integra", 2025, "A-Spec", "Sedan", "Lease", "Gas", 389, 2500, 36, 12000, 36900, 35400, 0.00140, 60, "Apex Blue", "Austin, TX", "Acura Austin", 0),
    ("Volvo", "XC60", 2025, "Plus B5", "SUV", "Lease", "Hybrid", 569, 3995, 36, 10000, 52900, 50600, 0.00160, 57, "Crystal White", "Seattle, WA", "Volvo Seattle", 0),
    ("Porsche", "Macan", 2025, "Base", "SUV", "Lease", "Gas", 879, 6500, 36, 10000, 68900, 67100, 0.00200, 60, "Carrara White", "Newport Beach, CA", "Porsche Newport", 1),
    ("Genesis", "GV70", 2025, "2.5T Advanced", "SUV", "Lease", "Gas", 599, 3999, 36, 10000, 54100, 51700, 0.00150, 58, "Uyuni White", "Scottsdale, AZ", "Genesis Scottsdale", 0),
    ("Toyota", "Camry", 2025, "XSE", "Sedan", "Lease", "Hybrid", 339, 2495, 36, 12000, 35600, 34200, 0.00130, 61, "Reservoir Blue", "Fresno, CA", "Toyota Fresno", 0),
    ("Toyota", "Tacoma", 2025, "TRD Sport", "Truck", "Finance", "Gas", 569, 3500, 72, None, 46800, 45100, None, None, "Celestial Silver", "Albuquerque, NM", "Toyota ABQ", 0),
    ("Rivian", "R1S", 2026, "Dual Motor", "SUV", "Cash", "Electric", None, None, None, None, 77900, 76500, None, None, "Forest Green", "Los Angeles, CA", "Rivian South Coast", 1),
    ("Toyota", "Corolla", 2025, "LE", "Sedan", "Cash", "Gas", None, None, None, None, 24200, 23400, None, None, "Classic Silver", "San Antonio, TX", "Toyota San Antonio", 0),
]

_COLUMNS = [
    "make", "model", "year", "trim", "body_type", "deal_type", "fuel_type",
    "monthly_payment", "down_payment", "term_months", "annual_mileage",
    "msrp", "selling_price", "money_factor", "residual_percent",
    "exterior_color", "location", "dealer_name", "featured",
]


def sample_dataframe() -> pd.DataFrame:
    df = pd.DataFrame(_ROWS, columns=_COLUMNS)
    df["description"] = ""
    df["status"] = "active"
    return df


def sample_records() -> list[dict]:
    return sample_dataframe().to_dict(orient="records")


def seed_if_empty() -> int:
    db.init_db()
    if db.count_listings() == 0:
        return db.bulk_insert(sample_records())
    return 0


def sample_csv_bytes() -> bytes:
    return sample_dataframe().to_csv(index=False).encode("utf-8")


def template_csv_bytes() -> bytes:
    """Header + two example rows showing the expected upload format."""
    cols = db.EDITABLE_COLUMNS
    example = [
        {
            "make": "Toyota", "model": "RAV4", "year": 2025, "trim": "XLE",
            "body_type": "SUV", "deal_type": "Lease", "fuel_type": "Gas",
            "monthly_payment": 329, "down_payment": 1995, "term_months": 36,
            "annual_mileage": 12000, "msrp": 35420, "selling_price": 34100,
            "money_factor": 0.0015, "residual_percent": 62,
            "exterior_color": "Lunar Rock", "location": "Los Angeles, CA",
            "dealer_name": "Toyota of Downtown LA",
            "image_url": "", "description": "Loyalty + conquest cash applied",
            "featured": 1, "status": "active",
        },
        {
            "make": "Honda", "model": "Civic", "year": 2025, "trim": "Sport",
            "body_type": "Sedan", "deal_type": "Finance", "fuel_type": "Gas",
            "monthly_payment": 389, "down_payment": 0, "term_months": 60,
            "annual_mileage": "", "msrp": 28900, "selling_price": 27800,
            "money_factor": "", "residual_percent": "",
            "exterior_color": "Rallye Red", "location": "San Jose, CA",
            "dealer_name": "Capitol Honda",
            "image_url": "", "description": "0.9% APR financing",
            "featured": 0, "status": "active",
        },
    ]
    df = pd.DataFrame(example, columns=cols)
    return df.to_csv(index=False).encode("utf-8")
