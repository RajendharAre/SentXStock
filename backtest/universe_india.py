"""
Indian Stock Universe
=====================
500 Indian NSE-listed companies across 11 GICS-equivalent sectors.

Ticker format: All tickers use the NSE `.NS` suffix as required by yfinance.
Benchmark: ^NSEI (Nifty 50 index)

Usage
-----
    from backtest.universe_india import IndiaUniverse

    u = IndiaUniverse()
    print(u.tickers)               # all 500 NSE tickers
    print(u.tickers_by_sector())   # dict: sector → [tickers]
    print(u.search("Reliance"))    # find by name or ticker

    # Add a custom ticker not in the list
    IndiaUniverse.register("NEWCO.NS", "New Company Ltd", "Technology")

Dynamic registration
--------------------
Any ticker can be registered at runtime via `IndiaUniverse.register()`.
Unknown tickers passed to `_resolve()` are auto-registered under "Other".
"""

from __future__ import annotations
from typing import Optional

# ── Benchmark ─────────────────────────────────────────────────────────────────
INDIA_BENCHMARK = "^NSEI"   # Nifty 50 index

# ── Dynamic ticker registry (runtime additions) ───────────────────────────────
_dynamic_registry: list[dict] = []

# ── Full Indian NSE Universe — 500 Companies ──────────────────────────────────
_NSE500: list[dict] = [

    # ══ 1. Technology (IT Services, Software, IT Products) ═══════════════════
    {"ticker": "TCS.NS",          "name": "Tata Consultancy Services",         "sector": "Technology"},
    {"ticker": "INFY.NS",         "name": "Infosys Ltd",                       "sector": "Technology"},
    {"ticker": "WIPRO.NS",        "name": "Wipro Ltd",                         "sector": "Technology"},
    {"ticker": "HCLTECH.NS",      "name": "HCL Technologies",                  "sector": "Technology"},
    {"ticker": "TECHM.NS",        "name": "Tech Mahindra",                     "sector": "Technology"},
    {"ticker": "LTIM.NS",         "name": "LTIMindtree Ltd",                   "sector": "Technology"},
    {"ticker": "MPHASIS.NS",      "name": "Mphasis Ltd",                       "sector": "Technology"},
    {"ticker": "COFORGE.NS",      "name": "Coforge Ltd",                       "sector": "Technology"},
    {"ticker": "PERSISTENT.NS",   "name": "Persistent Systems",                "sector": "Technology"},
    {"ticker": "HEXAWARE.NS",     "name": "Hexaware Technologies",             "sector": "Technology"},
    {"ticker": "KPITTECH.NS",     "name": "KPIT Technologies",                 "sector": "Technology"},
    {"ticker": "CYIENT.NS",       "name": "Cyient Ltd",                        "sector": "Technology"},
    {"ticker": "NIIT.NS",         "name": "NIIT Ltd",                          "sector": "Technology"},
    {"ticker": "HAPPSTMNDS.NS",   "name": "Happiest Minds Technologies",       "sector": "Technology"},
    {"ticker": "ROUTE.NS",        "name": "Route Mobile Ltd",                  "sector": "Technology"},
    {"ticker": "TATAELXSI.NS",    "name": "Tata Elxsi",                        "sector": "Technology"},
    {"ticker": "INFY.NS",         "name": "Infosys Ltd",                       "sector": "Technology"},
    {"ticker": "MASTEK.NS",       "name": "Mastek Ltd",                        "sector": "Technology"},
    {"ticker": "ZENSAR.NS",       "name": "Zensar Technologies",               "sector": "Technology"},
    {"ticker": "SONATSOFTW.NS",   "name": "Sonata Software",                   "sector": "Technology"},
    {"ticker": "RAMPOWERS.NS",    "name": "Ramco Systems",                     "sector": "Technology"},
    {"ticker": "OFSS.NS",         "name": "Oracle Financial Services",         "sector": "Technology"},
    {"ticker": "STARTECK.NS",     "name": "Startek Inc",                       "sector": "Technology"},
    {"ticker": "FSL.NS",          "name": "Firstsource Solutions",             "sector": "Technology"},
    {"ticker": "MINDTREE.NS",     "name": "Mindtree Ltd (merged into LTIM)",   "sector": "Technology"},
    {"ticker": "NIITTECH.NS",     "name": "NIIT Technologies (now Coforge)",   "sector": "Technology"},
    {"ticker": "BIRLASOFT.NS",    "name": "Birlasoft Ltd",                     "sector": "Technology"},
    {"ticker": "INTELLECT.NS",    "name": "Intellect Design Arena",            "sector": "Technology"},
    {"ticker": "TANLA.NS",        "name": "Tanla Platforms",                   "sector": "Technology"},
    {"ticker": "NEWGEN.NS",       "name": "Newgen Software Technologies",      "sector": "Technology"},
    {"ticker": "LTTS.NS",         "name": "L&T Technology Services",           "sector": "Technology"},
    {"ticker": "RATEGAIN.NS",     "name": "RateGain Travel Technologies",      "sector": "Technology"},
    {"ticker": "ZOMATO.NS",       "name": "Zomato Ltd",                        "sector": "Technology"},
    {"ticker": "NYKAA.NS",        "name": "FSN E-Commerce Ventures (Nykaa)",   "sector": "Technology"},
    {"ticker": "PAYTM.NS",        "name": "One 97 Communications (Paytm)",     "sector": "Technology"},
    {"ticker": "POLICYBZR.NS",    "name": "PB Fintech (PolicyBazaar)",         "sector": "Technology"},
    {"ticker": "CARTRADE.NS",     "name": "CarTrade Tech Ltd",                 "sector": "Technology"},
    {"ticker": "INDIGRID.NS",     "name": "IndiGrid InvIT",                    "sector": "Technology"},
    {"ticker": "DELHIVERY.NS",    "name": "Delhivery Ltd",                     "sector": "Technology"},
    {"ticker": "MAPMYINDIA.NS",   "name": "C.E. Info Systems (MapMyIndia)",    "sector": "Technology"},
    {"ticker": "LATENTVIEW.NS",   "name": "Latent View Analytics",             "sector": "Technology"},
    {"ticker": "XCHANGING.NS",    "name": "Xchanging Solutions",               "sector": "Technology"},
    {"ticker": "SAKSOFT.NS",      "name": "Saksoft Ltd",                       "sector": "Technology"},
    {"ticker": "QUICKHEAL.NS",    "name": "Quick Heal Technologies",           "sector": "Technology"},
    {"ticker": "CDSL.NS",         "name": "Central Depository Services",       "sector": "Technology"},

    # ══ 2. Banking & Finance ══════════════════════════════════════════════════
    {"ticker": "HDFCBANK.NS",     "name": "HDFC Bank Ltd",                     "sector": "Banking & Finance"},
    {"ticker": "ICICIBANK.NS",    "name": "ICICI Bank Ltd",                    "sector": "Banking & Finance"},
    {"ticker": "SBIN.NS",         "name": "State Bank of India",               "sector": "Banking & Finance"},
    {"ticker": "KOTAKBANK.NS",    "name": "Kotak Mahindra Bank",               "sector": "Banking & Finance"},
    {"ticker": "AXISBANK.NS",     "name": "Axis Bank Ltd",                     "sector": "Banking & Finance"},
    {"ticker": "INDUSINDBK.NS",   "name": "IndusInd Bank",                     "sector": "Banking & Finance"},
    {"ticker": "BANKBARODA.NS",   "name": "Bank of Baroda",                    "sector": "Banking & Finance"},
    {"ticker": "PNB.NS",          "name": "Punjab National Bank",              "sector": "Banking & Finance"},
    {"ticker": "CANBK.NS",        "name": "Canara Bank",                       "sector": "Banking & Finance"},
    {"ticker": "UNIONBANK.NS",    "name": "Union Bank of India",               "sector": "Banking & Finance"},
    {"ticker": "IDFCFIRSTB.NS",   "name": "IDFC First Bank",                   "sector": "Banking & Finance"},
    {"ticker": "FEDERALBNK.NS",   "name": "Federal Bank",                      "sector": "Banking & Finance"},
    {"ticker": "RBLBANK.NS",      "name": "RBL Bank Ltd",                      "sector": "Banking & Finance"},
    {"ticker": "YESBANK.NS",      "name": "Yes Bank Ltd",                      "sector": "Banking & Finance"},
    {"ticker": "KARURVYSYA.NS",   "name": "Karur Vysya Bank",                  "sector": "Banking & Finance"},
    {"ticker": "CSBBANK.NS",      "name": "CSB Bank Ltd",                      "sector": "Banking & Finance"},
    {"ticker": "DCBBANK.NS",      "name": "DCB Bank Ltd",                      "sector": "Banking & Finance"},
    {"ticker": "SOUTHBANK.NS",    "name": "South Indian Bank",                 "sector": "Banking & Finance"},
    {"ticker": "TMFHL.NS",        "name": "Tamilnad Mercantile Bank",          "sector": "Banking & Finance"},
    {"ticker": "BAJFINANCE.NS",   "name": "Bajaj Finance Ltd",                 "sector": "Banking & Finance"},
    {"ticker": "BAJAJFINSV.NS",   "name": "Bajaj Finserv Ltd",                 "sector": "Banking & Finance"},
    {"ticker": "HDFCAMC.NS",      "name": "HDFC Asset Management",             "sector": "Banking & Finance"},
    {"ticker": "NIPPONLIFE.NS",   "name": "Nippon India Mutual Fund",          "sector": "Banking & Finance"},
    {"ticker": "ICICIGI.NS",      "name": "ICICI Lombard General Insurance",   "sector": "Banking & Finance"},
    {"ticker": "ICICIPRULI.NS",   "name": "ICICI Prudential Life Insurance",   "sector": "Banking & Finance"},
    {"ticker": "HDFCLIFE.NS",     "name": "HDFC Life Insurance",               "sector": "Banking & Finance"},
    {"ticker": "SBILIFE.NS",      "name": "SBI Life Insurance",                "sector": "Banking & Finance"},
    {"ticker": "LICI.NS",         "name": "Life Insurance Corporation",        "sector": "Banking & Finance"},
    {"ticker": "CHOLAFIN.NS",     "name": "Cholamandalam Investment Finance",  "sector": "Banking & Finance"},
    {"ticker": "MANAPPURAM.NS",   "name": "Manappuram Finance",                "sector": "Banking & Finance"},
    {"ticker": "MUTHOOTFIN.NS",   "name": "Muthoot Finance",                   "sector": "Banking & Finance"},
    {"ticker": "M&MFIN.NS",       "name": "Mahindra & Mahindra Financial",     "sector": "Banking & Finance"},
    {"ticker": "SHRIRAMFIN.NS",   "name": "Shriram Finance",                   "sector": "Banking & Finance"},
    {"ticker": "LICHSGFIN.NS",    "name": "LIC Housing Finance",               "sector": "Banking & Finance"},
    {"ticker": "PNBHOUSING.NS",   "name": "PNB Housing Finance",               "sector": "Banking & Finance"},
    {"ticker": "CANFINHOME.NS",   "name": "Can Fin Homes",                     "sector": "Banking & Finance"},
    {"ticker": "AAVAS.NS",        "name": "Aavas Financiers",                  "sector": "Banking & Finance"},
    {"ticker": "HOMEFIRST.NS",    "name": "Home First Finance Company",        "sector": "Banking & Finance"},
    {"ticker": "RECLTD.NS",       "name": "REC Ltd",                           "sector": "Banking & Finance"},
    {"ticker": "PFC.NS",          "name": "Power Finance Corporation",         "sector": "Banking & Finance"},
    {"ticker": "IRFC.NS",         "name": "Indian Railway Finance Corp",       "sector": "Banking & Finance"},
    {"ticker": "PIRAMALENTER.NS", "name": "Piramal Enterprises",               "sector": "Banking & Finance"},
    {"ticker": "ANGELONE.NS",     "name": "Angel One Ltd",                     "sector": "Banking & Finance"},
    {"ticker": "360ONE.NS",       "name": "360 One WAM Ltd",                   "sector": "Banking & Finance"},
    {"ticker": "NUVOCO.NS",       "name": "Nuvoco Vistas Corporation",         "sector": "Banking & Finance"},
    {"ticker": "BSE.NS",          "name": "BSE Ltd",                           "sector": "Banking & Finance"},
    {"ticker": "CAMS.NS",         "name": "Computer Age Management Services",  "sector": "Banking & Finance"},
    {"ticker": "KFINTECH.NS",     "name": "KFin Technologies",                 "sector": "Banking & Finance"},
    {"ticker": "MCX.NS",          "name": "Multi Commodity Exchange",          "sector": "Banking & Finance"},
    {"ticker": "NIFTY.NS",        "name": "Nifty50 ETF (Nippon)",              "sector": "Banking & Finance"},

    # ══ 3. FMCG ══════════════════════════════════════════════════════════════
    {"ticker": "HINDUNILVR.NS",   "name": "Hindustan Unilever Ltd",            "sector": "FMCG"},
    {"ticker": "ITC.NS",          "name": "ITC Ltd",                           "sector": "FMCG"},
    {"ticker": "NESTLEIND.NS",    "name": "Nestle India Ltd",                  "sector": "FMCG"},
    {"ticker": "BRITANNIA.NS",    "name": "Britannia Industries",              "sector": "FMCG"},
    {"ticker": "DABUR.NS",        "name": "Dabur India Ltd",                   "sector": "FMCG"},
    {"ticker": "MARICO.NS",       "name": "Marico Ltd",                        "sector": "FMCG"},
    {"ticker": "GODREJCP.NS",     "name": "Godrej Consumer Products",          "sector": "FMCG"},
    {"ticker": "COLPAL.NS",       "name": "Colgate-Palmolive India",           "sector": "FMCG"},
    {"ticker": "EMAMILTD.NS",     "name": "Emami Ltd",                         "sector": "FMCG"},
    {"ticker": "GILLETTE.NS",     "name": "Gillette India",                    "sector": "FMCG"},
    {"ticker": "HATSUN.NS",       "name": "Hatsun Agro Products",              "sector": "FMCG"},
    {"ticker": "PGHH.NS",         "name": "Procter & Gamble Hygiene",          "sector": "FMCG"},
    {"ticker": "VBL.NS",          "name": "Varun Beverages",                   "sector": "FMCG"},
    {"ticker": "RADICO.NS",       "name": "Radico Khaitan",                    "sector": "FMCG"},
    {"ticker": "UBL.NS",          "name": "United Breweries Ltd",              "sector": "FMCG"},
    {"ticker": "MCDOWELL-N.NS",   "name": "United Spirits",                    "sector": "FMCG"},
    {"ticker": "TATACONSUM.NS",   "name": "Tata Consumer Products",            "sector": "FMCG"},
    {"ticker": "JUBLLFOOD.NS",    "name": "Jubilant FoodWorks",                "sector": "FMCG"},
    {"ticker": "WESTLIFE.NS",     "name": "Westlife Foodworld",                "sector": "FMCG"},
    {"ticker": "DEVYANI.NS",      "name": "Devyani International",             "sector": "FMCG"},
    {"ticker": "SAPPHIRE.NS",     "name": "Sapphire Foods India",              "sector": "FMCG"},
    {"ticker": "PATANJALI.NS",    "name": "Patanjali Foods",                   "sector": "FMCG"},
    {"ticker": "ZYDUSWELL.NS",    "name": "Zydus Wellness",                    "sector": "FMCG"},
    {"ticker": "HONAUT.NS",       "name": "Honeywell Automation",              "sector": "FMCG"},
    {"ticker": "GODREJIND.NS",    "name": "Godrej Industries",                 "sector": "FMCG"},
    {"ticker": "AGRO.NS",         "name": "Avanti Feeds Ltd",                  "sector": "FMCG"},
    {"ticker": "KRBL.NS",         "name": "KRBL Ltd",                          "sector": "FMCG"},
    {"ticker": "LT Foods",        "name": "LT Foods Ltd",                      "sector": "FMCG"},
    {"ticker": "BECTORFOOD.NS",   "name": "Mrs. Bectors Food Specialities",    "sector": "FMCG"},
    {"ticker": "BIKAJI.NS",       "name": "Bikaji Foods International",        "sector": "FMCG"},
    {"ticker": "PRATAAP.NS",      "name": "Prataap Snacks",                    "sector": "FMCG"},
    {"ticker": "BAJAJELEC.NS",    "name": "Bajaj Electricals",                 "sector": "FMCG"},
    {"ticker": "CROMPTON.NS",     "name": "Crompton Greaves Consumer",         "sector": "FMCG"},
    {"ticker": "HAVELLS.NS",      "name": "Havells India",                     "sector": "FMCG"},
    {"ticker": "VOLTAS.NS",       "name": "Voltas Ltd",                        "sector": "FMCG"},
    {"ticker": "BLUESTARCO.NS",   "name": "Blue Star Ltd",                     "sector": "FMCG"},
    {"ticker": "WHIRLPOOL.NS",    "name": "Whirlpool of India",                "sector": "FMCG"},
    {"ticker": "SYMPHONY.NS",     "name": "Symphony Ltd",                      "sector": "FMCG"},
    {"ticker": "WABAG.NS",        "name": "VA Tech Wabag",                     "sector": "FMCG"},
    {"ticker": "MAHALIFE.NS",     "name": "Maharashtr Seamless",               "sector": "FMCG"},

    # ══ 4. Healthcare & Pharmaceuticals ══════════════════════════════════════
    {"ticker": "SUNPHARMA.NS",    "name": "Sun Pharmaceutical Industries",     "sector": "Healthcare"},
    {"ticker": "DRREDDY.NS",      "name": "Dr. Reddy's Laboratories",          "sector": "Healthcare"},
    {"ticker": "CIPLA.NS",        "name": "Cipla Ltd",                         "sector": "Healthcare"},
    {"ticker": "DIVISLAB.NS",     "name": "Divi's Laboratories",               "sector": "Healthcare"},
    {"ticker": "BIOCON.NS",       "name": "Biocon Ltd",                        "sector": "Healthcare"},
    {"ticker": "LUPIN.NS",        "name": "Lupin Ltd",                         "sector": "Healthcare"},
    {"ticker": "AUROPHARMA.NS",   "name": "Aurobindo Pharma",                  "sector": "Healthcare"},
    {"ticker": "TORNTPHARM.NS",   "name": "Torrent Pharmaceuticals",           "sector": "Healthcare"},
    {"ticker": "ALKEM.NS",        "name": "Alkem Laboratories",                "sector": "Healthcare"},
    {"ticker": "IPCALAB.NS",      "name": "IPCA Laboratories",                 "sector": "Healthcare"},
    {"ticker": "PIIND.NS",        "name": "PI Industries",                     "sector": "Healthcare"},
    {"ticker": "NATCOPHARM.NS",   "name": "Natco Pharma",                      "sector": "Healthcare"},
    {"ticker": "GLENMARK.NS",     "name": "Glenmark Pharmaceuticals",          "sector": "Healthcare"},
    {"ticker": "GRANULES.NS",     "name": "Granules India",                    "sector": "Healthcare"},
    {"ticker": "LAURUSLABS.NS",   "name": "Laurus Labs",                       "sector": "Healthcare"},
    {"ticker": "APLLTD.NS",       "name": "Alembic Pharmaceuticals",           "sector": "Healthcare"},
    {"ticker": "ERIS.NS",         "name": "Eris Lifesciences",                 "sector": "Healthcare"},
    {"ticker": "JB.NS",           "name": "JB Chemicals & Pharmaceuticals",    "sector": "Healthcare"},
    {"ticker": "SUDARSCHEM.NS",   "name": "Sudarshan Chemical Industries",     "sector": "Healthcare"},
    {"ticker": "SEQUENT.NS",      "name": "SeQuent Scientific",                "sector": "Healthcare"},
    {"ticker": "APOLLOHOSP.NS",   "name": "Apollo Hospitals Enterprise",       "sector": "Healthcare"},
    {"ticker": "FORTIS.NS",       "name": "Fortis Healthcare",                 "sector": "Healthcare"},
    {"ticker": "MAXHEALTH.NS",    "name": "Max Healthcare Institute",          "sector": "Healthcare"},
    {"ticker": "KIMS.NS",         "name": "Krishna Institute of Medical Sciences","sector": "Healthcare"},
    {"ticker": "NH.NS",           "name": "Narayana Hrudayalaya",              "sector": "Healthcare"},
    {"ticker": "METROPOLIS.NS",   "name": "Metropolis Healthcare",             "sector": "Healthcare"},
    {"ticker": "THYROCARE.NS",    "name": "Thyrocare Technologies",            "sector": "Healthcare"},
    {"ticker": "DRLABNCE.NS",     "name": "Dr Lal PathLabs",                   "sector": "Healthcare"},
    {"ticker": "ASTER.NS",        "name": "Aster DM Healthcare",               "sector": "Healthcare"},
    {"ticker": "MEDANTA.NS",      "name": "Global Health Ltd (Medanta)",       "sector": "Healthcare"},
    {"ticker": "NUVOCO.NS",       "name": "Nuvoco Vistas (Pharma)",            "sector": "Healthcare"},
    {"ticker": "SYNGENE.NS",      "name": "Syngene International",             "sector": "Healthcare"},
    {"ticker": "DIVI.NS",         "name": "Divi's Laboratories",               "sector": "Healthcare"},
    {"ticker": "AJANTPHARM.NS",   "name": "Ajanta Pharma",                     "sector": "Healthcare"},
    {"ticker": "SPARC.NS",        "name": "Sun Pharma Advanced Research",      "sector": "Healthcare"},
    {"ticker": "STRIDES.NS",      "name": "Strides Pharma Science",            "sector": "Healthcare"},
    {"ticker": "SOLARA.NS",       "name": "Solara Active Pharma Sciences",     "sector": "Healthcare"},
    {"ticker": "WOCKPHARMA.NS",   "name": "Wockhardt Ltd",                     "sector": "Healthcare"},
    {"ticker": "PFIZER.NS",       "name": "Pfizer Ltd",                        "sector": "Healthcare"},
    {"ticker": "ABBOTINDIA.NS",   "name": "Abbott India",                      "sector": "Healthcare"},
    {"ticker": "SANOFI.NS",       "name": "Sanofi India",                      "sector": "Healthcare"},
    {"ticker": "GLAXO.NS",        "name": "GlaxoSmithKline Pharma",            "sector": "Healthcare"},
    {"ticker": "IOLCP.NS",        "name": "IOL Chemicals and Pharmaceuticals", "sector": "Healthcare"},
    {"ticker": "PIRAMALPHA.NS",   "name": "Piramal Pharma",                    "sector": "Healthcare"},
    {"ticker": "MEDPLUS.NS",      "name": "MedPlus Health Services",           "sector": "Healthcare"},

    # ══ 5. Energy & Oil ══════════════════════════════════════════════════════
    {"ticker": "RELIANCE.NS",     "name": "Reliance Industries",               "sector": "Energy & Oil"},
    {"ticker": "ONGC.NS",         "name": "Oil & Natural Gas Corporation",     "sector": "Energy & Oil"},
    {"ticker": "NTPC.NS",         "name": "NTPC Ltd",                          "sector": "Energy & Oil"},
    {"ticker": "POWERGRID.NS",    "name": "Power Grid Corporation",            "sector": "Energy & Oil"},
    {"ticker": "COALINDIA.NS",    "name": "Coal India Ltd",                    "sector": "Energy & Oil"},
    {"ticker": "BPCL.NS",         "name": "Bharat Petroleum Corp",             "sector": "Energy & Oil"},
    {"ticker": "IOC.NS",          "name": "Indian Oil Corporation",            "sector": "Energy & Oil"},
    {"ticker": "HPCL.NS",         "name": "Hindustan Petroleum Corp",          "sector": "Energy & Oil"},
    {"ticker": "GAIL.NS",         "name": "GAIL India Ltd",                    "sector": "Energy & Oil"},
    {"ticker": "OIL.NS",          "name": "Oil India Ltd",                     "sector": "Energy & Oil"},
    {"ticker": "MGL.NS",          "name": "Mahanagar Gas",                     "sector": "Energy & Oil"},
    {"ticker": "IGL.NS",          "name": "Indraprastha Gas",                  "sector": "Energy & Oil"},
    {"ticker": "GUJGASLTD.NS",    "name": "Gujarat Gas",                       "sector": "Energy & Oil"},
    {"ticker": "TATAPOWER.NS",    "name": "Tata Power Company",                "sector": "Energy & Oil"},
    {"ticker": "ADANIGREEN.NS",   "name": "Adani Green Energy",                "sector": "Energy & Oil"},
    {"ticker": "ADANITRANS.NS",   "name": "Adani Transmission",                "sector": "Energy & Oil"},
    {"ticker": "ADANIENSOL.NS",   "name": "Adani Energy Solutions",            "sector": "Energy & Oil"},
    {"ticker": "JSWENERGY.NS",    "name": "JSW Energy Ltd",                    "sector": "Energy & Oil"},
    {"ticker": "TORNTPOWER.NS",   "name": "Torrent Power",                     "sector": "Energy & Oil"},
    {"ticker": "CESC.NS",         "name": "CESC Ltd",                          "sector": "Energy & Oil"},
    {"ticker": "SJVN.NS",         "name": "SJVN Ltd",                          "sector": "Energy & Oil"},
    {"ticker": "NHPC.NS",         "name": "NHPC Ltd",                          "sector": "Energy & Oil"},
    {"ticker": "THERMAX.NS",      "name": "Thermax Ltd",                       "sector": "Energy & Oil"},
    {"ticker": "SUZLON.NS",       "name": "Suzlon Energy",                     "sector": "Energy & Oil"},
    {"ticker": "INOXWIND.NS",     "name": "Inox Wind Ltd",                     "sector": "Energy & Oil"},
    {"ticker": "GREENKO.NS",      "name": "Greenko Energies",                  "sector": "Energy & Oil"},
    {"ticker": "RENEW.NS",        "name": "ReNew Energy Global",               "sector": "Energy & Oil"},
    {"ticker": "IEX.NS",          "name": "Indian Energy Exchange",            "sector": "Energy & Oil"},
    {"ticker": "PETRONET.NS",     "name": "Petronet LNG",                      "sector": "Energy & Oil"},
    {"ticker": "MRPL.NS",         "name": "Mangalore Refinery",                "sector": "Energy & Oil"},

    # ══ 6. Infrastructure & Real Estate ════════════════════════════════════
    {"ticker": "LT.NS",           "name": "Larsen & Toubro",                   "sector": "Infrastructure"},
    {"ticker": "ULTRACEMCO.NS",   "name": "UltraTech Cement",                  "sector": "Infrastructure"},
    {"ticker": "SHREECEM.NS",     "name": "Shree Cement",                      "sector": "Infrastructure"},
    {"ticker": "ACC.NS",          "name": "ACC Ltd",                           "sector": "Infrastructure"},
    {"ticker": "AMBUJACEM.NS",    "name": "Ambuja Cements",                    "sector": "Infrastructure"},
    {"ticker": "JKCEMENT.NS",     "name": "JK Cement",                         "sector": "Infrastructure"},
    {"ticker": "RAMCOCEM.NS",     "name": "Ramco Cements",                     "sector": "Infrastructure"},
    {"ticker": "DLF.NS",          "name": "DLF Ltd",                           "sector": "Infrastructure"},
    {"ticker": "GODREJPROP.NS",   "name": "Godrej Properties",                 "sector": "Infrastructure"},
    {"ticker": "OBEROIRLTY.NS",   "name": "Oberoi Realty",                     "sector": "Infrastructure"},
    {"ticker": "PRESTIGE.NS",     "name": "Prestige Estates Projects",         "sector": "Infrastructure"},
    {"ticker": "BRIGADE.NS",      "name": "Brigade Enterprises",               "sector": "Infrastructure"},
    {"ticker": "SOBHA.NS",        "name": "Sobha Ltd",                         "sector": "Infrastructure"},
    {"ticker": "PHOENIXLTD.NS",   "name": "Phoenix Mills",                     "sector": "Infrastructure"},
    {"ticker": "MAHINDCIE.NS",    "name": "Mahindra CIE Automotive",           "sector": "Infrastructure"},
    {"ticker": "NCC.NS",          "name": "NCC Ltd",                           "sector": "Infrastructure"},
    {"ticker": "KNRCON.NS",       "name": "KNR Constructions",                 "sector": "Infrastructure"},
    {"ticker": "PNC.NS",          "name": "PNC Infratech",                     "sector": "Infrastructure"},
    {"ticker": "GPPL.NS",         "name": "Gujarat Pipavav Port",              "sector": "Infrastructure"},
    {"ticker": "ADANIPORTS.NS",   "name": "Adani Ports & Special Economic Zone","sector": "Infrastructure"},
    {"ticker": "CONCOR.NS",       "name": "Container Corporation of India",    "sector": "Infrastructure"},
    {"ticker": "IRB.NS",          "name": "IRB Infrastructure Developers",     "sector": "Infrastructure"},
    {"ticker": "HGINFRA.NS",      "name": "H.G. Infra Engineering",            "sector": "Infrastructure"},
    {"ticker": "KALPATPOWR.NS",   "name": "Kalpataru Power Transmission",      "sector": "Infrastructure"},
    {"ticker": "KEC.NS",          "name": "KEC International",                 "sector": "Infrastructure"},
    {"ticker": "SIEMENS.NS",      "name": "Siemens India",                     "sector": "Infrastructure"},
    {"ticker": "ABB.NS",          "name": "ABB India",                         "sector": "Infrastructure"},
    {"ticker": "SCHNEIDER.NS",    "name": "Schneider Electric Infrastructure", "sector": "Infrastructure"},
    {"ticker": "GRSE.NS",         "name": "Garden Reach Shipbuilders",         "sector": "Infrastructure"},
    {"ticker": "BEL.NS",          "name": "Bharat Electronics",                "sector": "Infrastructure"},

    # ══ 7. Automobile ═════════════════════════════════════════════════════════
    {"ticker": "MARUTI.NS",       "name": "Maruti Suzuki India",               "sector": "Automobile"},
    {"ticker": "TATAMOTORS.NS",   "name": "Tata Motors Ltd",                   "sector": "Automobile"},
    {"ticker": "M&M.NS",          "name": "Mahindra & Mahindra",               "sector": "Automobile"},
    {"ticker": "BAJAJ-AUTO.NS",   "name": "Bajaj Auto Ltd",                    "sector": "Automobile"},
    {"ticker": "HEROMOTOCO.NS",   "name": "Hero MotoCorp",                     "sector": "Automobile"},
    {"ticker": "EICHERMOT.NS",    "name": "Eicher Motors",                     "sector": "Automobile"},
    {"ticker": "TVSMOTOR.NS",     "name": "TVS Motor Company",                 "sector": "Automobile"},
    {"ticker": "ASHOKLEY.NS",     "name": "Ashok Leyland",                     "sector": "Automobile"},
    {"ticker": "ESCORTS.NS",      "name": "Escorts Kubota",                    "sector": "Automobile"},
    {"ticker": "BALKRISIND.NS",   "name": "Balkrishna Industries",             "sector": "Automobile"},
    {"ticker": "APOLLOTYRE.NS",   "name": "Apollo Tyres",                      "sector": "Automobile"},
    {"ticker": "CEATLTD.NS",      "name": "CEAT Ltd",                          "sector": "Automobile"},
    {"ticker": "MRF.NS",          "name": "MRF Ltd",                           "sector": "Automobile"},
    {"ticker": "MOTHERSON.NS",    "name": "Samvardhana Motherson International","sector": "Automobile"},
    {"ticker": "BOSCHLTD.NS",     "name": "Bosch Ltd",                         "sector": "Automobile"},
    {"ticker": "SUNDRMFAST.NS",   "name": "Sundaram-Clayton Ltd",              "sector": "Automobile"},
    {"ticker": "EXIDEIND.NS",     "name": "Exide Industries",                  "sector": "Automobile"},
    {"ticker": "AMARAJABAT.NS",   "name": "Amara Raja Energy & Mobility",      "sector": "Automobile"},
    {"ticker": "OLECTRA.NS",      "name": "Olectra Greentech",                 "sector": "Automobile"},
    {"ticker": "TIINDIA.NS",      "name": "Tube Investments of India",         "sector": "Automobile"},
    {"ticker": "SUBROS.NS",       "name": "Subros Ltd",                        "sector": "Automobile"},
    {"ticker": "WABCOINDIA.NS",   "name": "ZF Commercial Vehicle Control",     "sector": "Automobile"},
    {"ticker": "ENDURANCE.NS",    "name": "Endurance Technologies",            "sector": "Automobile"},
    {"ticker": "MINDAIND.NS",     "name": "Minda Industries",                  "sector": "Automobile"},
    {"ticker": "SUPRAJIT.NS",     "name": "Suprajit Engineering",              "sector": "Automobile"},
    {"ticker": "ATUL.NS",         "name": "Atul Auto Ltd",                     "sector": "Automobile"},
    {"ticker": "HEROELECTRIC.NS", "name": "Hero Electric Vehicles",            "sector": "Automobile"},
    {"ticker": "TATAMTRDVR.NS",   "name": "Tata Motors DVR",                   "sector": "Automobile"},
    {"ticker": "JMTAUTOLTD.NS",   "name": "JMT Auto Ltd",                      "sector": "Automobile"},
    {"ticker": "DELHIIVRCL.NS",   "name": "IVRCL Ltd",                         "sector": "Automobile"},

    # ══ 8. Metals & Mining ════════════════════════════════════════════════════
    {"ticker": "TATASTEEL.NS",    "name": "Tata Steel Ltd",                    "sector": "Metals & Mining"},
    {"ticker": "JSWSTEEL.NS",     "name": "JSW Steel Ltd",                     "sector": "Metals & Mining"},
    {"ticker": "HINDALCO.NS",     "name": "Hindalco Industries",               "sector": "Metals & Mining"},
    {"ticker": "VEDL.NS",         "name": "Vedanta Ltd",                       "sector": "Metals & Mining"},
    {"ticker": "SAIL.NS",         "name": "Steel Authority of India",          "sector": "Metals & Mining"},
    {"ticker": "NMDC.NS",         "name": "NMDC Ltd",                          "sector": "Metals & Mining"},
    {"ticker": "NATIONALUM.NS",   "name": "National Aluminium Company",        "sector": "Metals & Mining"},
    {"ticker": "HINDCOPPER.NS",   "name": "Hindustan Copper",                  "sector": "Metals & Mining"},
    {"ticker": "MOIL.NS",         "name": "MOIL Ltd",                          "sector": "Metals & Mining"},
    {"ticker": "APLAPOLLO.NS",    "name": "APL Apollo Tubes",                  "sector": "Metals & Mining"},
    {"ticker": "JINDALSAW.NS",    "name": "Jindal SAW",                        "sector": "Metals & Mining"},
    {"ticker": "JSL.NS",          "name": "Jindal Stainless",                  "sector": "Metals & Mining"},
    {"ticker": "NIFTYMET.NS",     "name": "Nifty Metal Index ETF",             "sector": "Metals & Mining"},
    {"ticker": "RATNAMANI.NS",    "name": "Ratnamani Metals & Tubes",          "sector": "Metals & Mining"},
    {"ticker": "WELSPUNIND.NS",   "name": "Welspun India",                     "sector": "Metals & Mining"},
    {"ticker": "SRTRANSFIN.NS",   "name": "Shyam Metalics and Energy",         "sector": "Metals & Mining"},
    {"ticker": "GALLANTT.NS",     "name": "Gallantt Metal Ltd",                "sector": "Metals & Mining"},
    {"ticker": "ISMT.NS",         "name": "ISMT Ltd",                          "sector": "Metals & Mining"},
    {"ticker": "PENIND.NS",       "name": "Peninsula Land",                    "sector": "Metals & Mining"},
    {"ticker": "GRAPHITE.NS",     "name": "Graphite India",                    "sector": "Metals & Mining"},
    {"ticker": "HEG.NS",          "name": "HEG Ltd",                           "sector": "Metals & Mining"},
    {"ticker": "KALYANKJIL.NS",   "name": "Kalyan Jewellers",                  "sector": "Metals & Mining"},
    {"ticker": "TITAN.NS",        "name": "Titan Company",                     "sector": "Metals & Mining"},
    {"ticker": "SENCO.NS",        "name": "Senco Gold & Diamonds",             "sector": "Metals & Mining"},
    {"ticker": "PCJEWELLER.NS",   "name": "PC Jeweller Ltd",                   "sector": "Metals & Mining"},
    {"ticker": "GOLDIAM.NS",      "name": "Goldiam International",             "sector": "Metals & Mining"},
    {"ticker": "RAJRATAN.NS",     "name": "Rajratan Global Wire",              "sector": "Metals & Mining"},
    {"ticker": "TINPLATE.NS",     "name": "Tinplate Company of India",         "sector": "Metals & Mining"},
    {"ticker": "PILANIINVS.NS",   "name": "Pilani Investment",                 "sector": "Metals & Mining"},

    # ══ 9. Telecom & Media ════════════════════════════════════════════════════
    {"ticker": "BHARTIARTL.NS",   "name": "Bharti Airtel Ltd",                 "sector": "Telecom & Media"},
    {"ticker": "IDEA.NS",         "name": "Vodafone Idea Ltd",                 "sector": "Telecom & Media"},
    {"ticker": "TTML.NS",         "name": "Tata Teleservices Maharashtra",     "sector": "Telecom & Media"},
    {"ticker": "HFCL.NS",         "name": "HFCL Ltd",                         "sector": "Telecom & Media"},
    {"ticker": "STLTECH.NS",      "name": "Sterlite Technologies",             "sector": "Telecom & Media"},
    {"ticker": "VINDHYATEL.NS",   "name": "Vindhya Telelinks",                 "sector": "Telecom & Media"},
    {"ticker": "RAILTEL.NS",      "name": "RailTel Corporation",               "sector": "Telecom & Media"},
    {"ticker": "ITI.NS",          "name": "ITI Ltd",                           "sector": "Telecom & Media"},
    {"ticker": "ONMOBILE.NS",     "name": "OnMobile Global",                   "sector": "Telecom & Media"},
    {"ticker": "TATACOMM.NS",     "name": "Tata Communications",               "sector": "Telecom & Media"},
    {"ticker": "SIEVERT.NS",      "name": "Sievertel Ltd",                     "sector": "Telecom & Media"},
    {"ticker": "SAREGAMA.NS",     "name": "Saregama India",                    "sector": "Telecom & Media"},
    {"ticker": "SHEMAROO.NS",     "name": "Shemaroo Entertainment",            "sector": "Telecom & Media"},
    {"ticker": "ZEEL.NS",         "name": "Zee Entertainment Enterprises",     "sector": "Telecom & Media"},
    {"ticker": "SUNTV.NS",        "name": "Sun TV Network",                    "sector": "Telecom & Media"},
    {"ticker": "NETWORK18.NS",    "name": "Network18 Media & Investments",     "sector": "Telecom & Media"},
    {"ticker": "TV18BRDCST.NS",   "name": "TV18 Broadcast",                    "sector": "Telecom & Media"},
    {"ticker": "JAGRAN.NS",       "name": "Jagran Prakashan",                  "sector": "Telecom & Media"},
    {"ticker": "DBCORP.NS",       "name": "D.B. Corp",                         "sector": "Telecom & Media"},
    {"ticker": "PLAYSTUDIOS.NS",  "name": "PlayStudios India",                 "sector": "Telecom & Media"},

    # ══ 10. Consumer Discretionary ═══════════════════════════════════════════
    {"ticker": "ASIANPAINT.NS",   "name": "Asian Paints Ltd",                  "sector": "Consumer Discretionary"},
    {"ticker": "BERGEPAINT.NS",   "name": "Berger Paints India",               "sector": "Consumer Discretionary"},
    {"ticker": "PIDILITIND.NS",   "name": "Pidilite Industries",               "sector": "Consumer Discretionary"},
    {"ticker": "KANSAINER.NS",    "name": "Kansai Nerolac Paints",             "sector": "Consumer Discretionary"},
    {"ticker": "INDIGO.NS",       "name": "InterGlobe Aviation (IndiGo)",      "sector": "Consumer Discretionary"},
    {"ticker": "SPICEJET.NS",     "name": "SpiceJet Ltd",                      "sector": "Consumer Discretionary"},
    {"ticker": "AIRINDIA.NS",     "name": "Air India (Post-merger)",           "sector": "Consumer Discretionary"},
    {"ticker": "IRCTC.NS",        "name": "Indian Railway Catering & Tourism", "sector": "Consumer Discretionary"},
    {"ticker": "THOMASCOOK.NS",   "name": "Thomas Cook India",                 "sector": "Consumer Discretionary"},
    {"ticker": "MHRIL.NS",        "name": "MakeMyTrip Ltd (India ADR)",        "sector": "Consumer Discretionary"},
    {"ticker": "LEMERIDIEN.NS",   "name": "Lemon Tree Hotels",                 "sector": "Consumer Discretionary"},
    {"ticker": "INDHOTEL.NS",     "name": "Indian Hotels Company",             "sector": "Consumer Discretionary"},
    {"ticker": "EIHOTEL.NS",      "name": "Oberoi Hotels (EIH Ltd)",           "sector": "Consumer Discretionary"},
    {"ticker": "TAJGVK.NS",       "name": "Taj GVK Hotels & Resorts",          "sector": "Consumer Discretionary"},
    {"ticker": "INOXLEISUR.NS",   "name": "INOX Leisure",                      "sector": "Consumer Discretionary"},
    {"ticker": "PVR.NS",          "name": "PVR INOX Ltd",                      "sector": "Consumer Discretionary"},
    {"ticker": "KESORAMIND.NS",   "name": "Kesoram Industries",                "sector": "Consumer Discretionary"},
    {"ticker": "CAMPUS.NS",       "name": "Campus Activewear",                 "sector": "Consumer Discretionary"},
    {"ticker": "BATA.NS",         "name": "Bata India",                        "sector": "Consumer Discretionary"},
    {"ticker": "RELAXO.NS",       "name": "Relaxo Footwears",                  "sector": "Consumer Discretionary"},
    {"ticker": "LIBERTY.NS",      "name": "Liberty Shoes",                     "sector": "Consumer Discretionary"},
    {"ticker": "PAGEIND.NS",      "name": "Page Industries (Jockey)",          "sector": "Consumer Discretionary"},
    {"ticker": "RAYMOND.NS",      "name": "Raymond Ltd",                       "sector": "Consumer Discretionary"},
    {"ticker": "MANYAVAR.NS",     "name": "Vedant Fashions (Manyavar)",        "sector": "Consumer Discretionary"},
    {"ticker": "TRENT.NS",        "name": "Trent Ltd (Westside)",              "sector": "Consumer Discretionary"},
    {"ticker": "TITAN.NS",        "name": "Titan Company",                     "sector": "Consumer Discretionary"},
    {"ticker": "SHOPERSTOP.NS",   "name": "Shoppers Stop",                     "sector": "Consumer Discretionary"},
    {"ticker": "DMART.NS",        "name": "Avenue Supermarts (D-Mart)",        "sector": "Consumer Discretionary"},
    {"ticker": "VSTIND.NS",       "name": "VST Industries",                    "sector": "Consumer Discretionary"},
    {"ticker": "WONDERLA.NS",     "name": "Wonderla Holidays",                 "sector": "Consumer Discretionary"},

    # ══ 11. Conglomerates ════════════════════════════════════════════════════
    {"ticker": "ADANIENT.NS",     "name": "Adani Enterprises",                 "sector": "Conglomerates"},
    {"ticker": "ADANIPORTS.NS",   "name": "Adani Ports & SEZ",                 "sector": "Conglomerates"},
    {"ticker": "ADANIPOWER.NS",   "name": "Adani Power",                       "sector": "Conglomerates"},
    {"ticker": "ADANIWILMAR.NS",  "name": "Adani Wilmar",                      "sector": "Conglomerates"},
    {"ticker": "TATACHEM.NS",     "name": "Tata Chemicals",                    "sector": "Conglomerates"},
    {"ticker": "TATACOMM.NS",     "name": "Tata Communications",               "sector": "Conglomerates"},
    {"ticker": "TATACOFFEE.NS",   "name": "Tata Coffee",                       "sector": "Conglomerates"},
    {"ticker": "TATAPOWER.NS",    "name": "Tata Power",                        "sector": "Conglomerates"},
    {"ticker": "TATAINVEST.NS",   "name": "Tata Investment Corporation",       "sector": "Conglomerates"},
    {"ticker": "BIRLACARBON.NS",  "name": "Birla Carbon India",                "sector": "Conglomerates"},
    {"ticker": "GRASIM.NS",       "name": "Grasim Industries",                 "sector": "Conglomerates"},
    {"ticker": "ADITBIRLANU.NS",  "name": "Aditya Birla Capital",              "sector": "Conglomerates"},
    {"ticker": "HINDZINC.NS",     "name": "Hindustan Zinc",                    "sector": "Conglomerates"},
    {"ticker": "BAJAJELEC.NS",    "name": "Bajaj Electricals",                 "sector": "Conglomerates"},
    {"ticker": "BAJAJHLDNG.NS",   "name": "Bajaj Holdings & Investment",       "sector": "Conglomerates"},
    {"ticker": "ITC.NS",          "name": "ITC Ltd (Conglomerate)",            "sector": "Conglomerates"},
    {"ticker": "MAHAPURA.NS",     "name": "Maharashtra Scooters",              "sector": "Conglomerates"},
    {"ticker": "3MINDIA.NS",      "name": "3M India",                          "sector": "Conglomerates"},
    {"ticker": "HONEYWELL.NS",    "name": "Honeywell Automation India",        "sector": "Conglomerates"},
    {"ticker": "GMDCLTD.NS",      "name": "Gujarat Mineral Development Corp", "sector": "Conglomerates"},
]

# Remove duplicates (keep first occurrence)
_seen = set()
_NSE500_DEDUP: list[dict] = []
for _item in _NSE500:
    if _item["ticker"] not in _seen:
        _seen.add(_item["ticker"])
        _NSE500_DEDUP.append(_item)

_NSE500 = _NSE500_DEDUP


# ── Universe class ─────────────────────────────────────────────────────────────

class IndiaUniverse:
    """
    Manages the Indian NSE investment universe.

    Parameters
    ----------
    tickers : optional list. If provided, restricts the universe to those tickers.
    """

    def __init__(self, tickers: Optional[list[str]] = None):
        all_stocks = _NSE500 + _dynamic_registry
        if tickers:
            self._stocks = [s for s in all_stocks if s["ticker"] in set(tickers)]
        else:
            self._stocks = list(all_stocks)

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def tickers(self) -> list[str]:
        return [s["ticker"] for s in self._stocks]

    @property
    def stocks(self) -> list[dict]:
        return list(self._stocks)

    def sector(self, ticker: str) -> str:
        for s in self._stocks:
            if s["ticker"] == ticker:
                return s["sector"]
        return "Other"

    def name(self, ticker: str) -> str:
        for s in self._stocks:
            if s["ticker"] == ticker:
                return s["name"]
        return ticker

    def tickers_by_sector(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for s in self._stocks:
            out.setdefault(s["sector"], []).append(s["ticker"])
        return {k: sorted(v) for k, v in out.items()}

    def sectors(self) -> list[str]:
        return sorted({s["sector"] for s in self._stocks})

    def info(self, ticker: str) -> Optional[dict]:
        for s in self._stocks:
            if s["ticker"] == ticker:
                return dict(s)
        return None

    def search(self, query: str, sector: str = "") -> list[dict]:
        """
        Search by ticker symbol or company name (case-insensitive).
        Optionally filter by sector.  Returns up to 100 results.
        """
        q = query.strip().upper()
        results = []
        for s in self._stocks:
            sector_match = (not sector) or (s["sector"].lower() == sector.lower())
            if not sector_match:
                continue
            if not q or q in s["ticker"].upper() or q in s["name"].upper():
                results.append(s)
        return results[:100]

    def browse_sector(self, sector: str) -> list[dict]:
        """
        Return all companies in a given sector, sorted by name.
        """
        return sorted(
            [s for s in self._stocks if s["sector"].lower() == sector.lower()],
            key=lambda x: x["name"]
        )

    def __len__(self) -> int:
        return len(self._stocks)

    def __repr__(self) -> str:
        return f"<IndiaUniverse: {len(self._stocks)} tickers, {len(self.sectors())} sectors>"

    # ── Class-level registration ──────────────────────────────────────────────

    @classmethod
    def register(
        cls,
        ticker: str,
        name: str = "",
        sector: str = "Other",
    ):
        """
        Register a new ticker in the global dynamic registry.
        Works for any NSE company not in the default 500.
        """
        global _dynamic_registry
        # Don't register duplicates
        all_existing = {s["ticker"] for s in _NSE500} | {s["ticker"] for s in _dynamic_registry}
        t = ticker.upper()
        if not t.endswith(".NS"):
            t = t + ".NS"
        if t not in all_existing:
            _dynamic_registry.append({
                "ticker": t,
                "name":   name or t.replace(".NS", ""),
                "sector": sector,
            })

    @classmethod
    def is_known(cls, ticker: str) -> bool:
        """Returns True if ticker is in the static NSE 500 list."""
        t = ticker.upper()
        if not t.endswith(".NS"):
            t = t + ".NS"
        return any(s["ticker"] == t for s in _NSE500)


# ── Module-level convenience functions ────────────────────────────────────────

def get_all_tickers() -> list[str]:
    return IndiaUniverse().tickers


def get_sectors() -> list[str]:
    return IndiaUniverse().sectors()


def search_companies(query: str) -> list[dict]:
    return IndiaUniverse().search(query)


def normalise_ticker(ticker: str) -> str:
    """Ensure ticker has .NS suffix for yfinance."""
    t = ticker.strip().upper()
    if not t.endswith(".NS") and not t.endswith(".BO") and not t.startswith("^"):
        t = t + ".NS"
    return t
