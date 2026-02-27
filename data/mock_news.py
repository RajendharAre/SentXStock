"""
Mock news headlines for fallback / demo mode.
"""

import random
from datetime import datetime, timedelta


def get_mock_news() -> list[dict]:
    """Return a list of mock financial news headlines."""
    return [
        {
            "source": "Reuters",
            "headline": "Tech stocks surge as AI chip demand hits record highs",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Bloomberg",
            "headline": "Federal Reserve signals potential rate cuts in upcoming quarter",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "CNBC",
            "headline": "Apple reports record quarterly revenue beating analyst expectations",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "earnings",
        },
        {
            "source": "Financial Times",
            "headline": "Oil prices drop sharply amid global demand concerns",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "Wall Street Journal",
            "headline": "Semiconductor shortage eases as new fabs come online",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "MarketWatch",
            "headline": "Consumer confidence index rises to 18-month high",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "Reuters",
            "headline": "Tesla deliveries miss expectations amid increasing competition",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "automotive",
        },
        {
            "source": "Bloomberg",
            "headline": "Gold prices climb as investors seek safe-haven assets",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "CNBC",
            "headline": "Microsoft Azure revenue growth accelerates cloud dominance",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Financial Times",
            "headline": "Banking sector faces pressure from rising default rates",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "finance",
        },
    ]


# ── Sector-aware headline templates ──────────────────────────────────────────

_SECTOR_TEMPLATES: dict[str, list[tuple[str, float]]] = {
    "Technology": [
        ("{n} wins large cloud services deal from government sector", 0.6),
        ("{n} expands AI capabilities with new product launch", 0.55),
        ("{n} Q3 revenue beats street estimates by 8%", 0.65),
        ("{n} announces strategic partnership with global tech giant", 0.5),
        ("{n} faces margin pressure amid rising employee costs", -0.35),
        ("{n} wins ₹1,200-crore contract from defence ministry", 0.7),
        ("{n} headcount reduction raises efficiency concerns", -0.4),
        ("{n} new product roadmap signals strong FY26 outlook", 0.6),
        ("{n} attrition improves to 12% — best in four quarters", 0.45),
        ("{n} guided higher on digital transformation demand", 0.5),
    ],
    "Banking & Finance": [
        ("{n} Q3 net profit up 18% YoY on strong loan growth", 0.65),
        ("{n} NPA ratio improves to 2.1%, analyst upgrade follows", 0.6),
        ("{n} raises ₹5,000 Cr via QIP at premium to market price", 0.45),
        ("{n} CASA ratio dips slightly amid competitive deposit rates", -0.3),
        ("{n} net interest margin expands 12 bps, beats consensus", 0.55),
        ("{n} credit card spends touch all-time high in holiday season", 0.5),
        ("{n} sets aside higher provisions on corporate book stress", -0.45),
        ("{n} RBI inspection finds minor compliance gaps", -0.4),
        ("{n} retail loan portfolio grows 24% YoY, analysts positive", 0.6),
        ("{n} acquires NBFC to deepen rural lending footprint", 0.4),
    ],
    "Healthcare": [
        ("{n} gets USFDA approval for key generics formulation", 0.75),
        ("{n} Q2 EBITDA margin expands 180 bps on operational leverage", 0.6),
        ("{n} launches biosimilar product in regulated markets", 0.55),
        ("{n} receives USFDA warning letter for API facility", -0.65),
        ("{n} hospital chain reports 95% bed occupancy in metros", 0.5),
        ("{n} wins tender for national immunisation programme", 0.55),
        ("{n} API unit faces pricing pressure from Chinese competitors", -0.4),
        ("{n} expands capacity with ₹800-Cr greenfield pharma plant", 0.4),
        ("{n} net revenue up 22% driven by chronic segment", 0.55),
        ("{n} clinical trial shows positive Phase 3 data", 0.7),
    ],
    "FMCG": [
        ("{n} volume growth of 9% beats expectations in rural markets", 0.6),
        ("{n} premium portfolio share rises to 42% of revenue", 0.5),
        ("{n} input cost tailwind to support margin expansion", 0.5),
        ("{n} Q2 ad-spend cuts weigh on brand equity perception", -0.35),
        ("{n} launches D2C platform targeting tier-2 cities", 0.45),
        ("{n} raw material inflation trims EBITDA margin by 80 bps", -0.4),
        ("{n} festive season sales up 18% YoY across categories", 0.6),
        ("{n} new product launches in health & wellness space", 0.5),
        ("{n} distribution reach expands to 7 million outlets", 0.4),
        ("{n} price hike of 4-6% to offset palm oil cost rise", 0.35),
    ],
    "Automobile": [
        ("{n} monthly wholesales up 15% YoY on strong EV demand", 0.65),
        ("{n} EV market share rises to 28% in SUV segment", 0.6),
        ("{n} global chip shortage eases; production back to normal", 0.5),
        ("{n} Q2 EBITDA margin contracts on discounting pressure", -0.4),
        ("{n} launches new mid-size SUV at aggressive price point", 0.55),
        ("{n} export volumes to Africa and ASEAN surge 32%", 0.5),
        ("{n} retains top position in PV segment for 7th straight month", 0.45),
        ("{n} sets FY26 EV sales target of 1 lakh units", 0.5),
        ("{n} recall of 45,000 units for brake system check", -0.55),
        ("{n} JV with global OEM for hydrogen fuel cell technology", 0.45),
    ],
    "Energy & Oil": [
        ("{n} refining margins at 3-year high on product spread", 0.6),
        ("{n} capex plan of ₹25,000 Cr over next 3 years", 0.4),
        ("{n} Q3 PAT up 28% driven by upstream crude prices", 0.55),
        ("{n} pipeline tariff hike approved by regulator", 0.45),
        ("{n} crude throughput at 101% capacity utilisation", 0.5),
        ("{n} faces environmental violation notice from pollution board", -0.55),
        ("{n} LNG import capacity expansion boosts energy security", 0.4),
        ("{n} city gas distribution expanded to 45 new districts", 0.45),
        ("{n} renewable energy JV attracts global PE interest", 0.5),
        ("{n} diesel cracks compress on global demand uncertainty", -0.35),
    ],
    "Metals & Mining": [
        ("{n} realisation per tonne improves 11% QoQ on China demand", 0.55),
        ("{n} capacity expansion of 2 MTPA on track for H1 FY27", 0.45),
        ("{n} EBITDA per tonne best in 6 quarters post cost cuts", 0.6),
        ("{n} ESG rating upgraded to A by global agency", 0.4),
        ("{n} inventory build-up weighs on near-term profitability", -0.4),
        ("{n} bauxite mine gets green clearance; volume visibility improves", 0.5),
        ("{n} coking coal price rise squeezes integrated margins", -0.45),
        ("{n} domestic steel demand lifts on infra spending", 0.55),
        ("{n} acquires Australian iron ore mine for supply security", 0.45),
        ("{n} LME nickel crash dents specialty metals realisation", -0.5),
    ],
    "Infrastructure": [
        ("{n} secures ₹3,200-Cr expressway EPC contract from NHAI", 0.65),
        ("{n} order book at all-time high of ₹55,000 Cr", 0.7),
        ("{n} execution picks up after monsoon delays; Q3 guidance intact", 0.5),
        ("{n} working capital cycle improves; D/E at three-year low", 0.55),
        ("{n} faces cost overruns on legacy hydro project", -0.45),
        ("{n} wins data-centre construction order from hyperscaler", 0.6),
        ("{n} EBITDA margin guidance upgraded to 14.5-15% for FY26", 0.5),
        ("{n} promoter stake sale to strategic investor", 0.4),
        ("{n} toll collection revenue up 18% on traffic normalisation", 0.5),
        ("{n} dispute with state government on receivables drags earnings", -0.5),
    ],
    "Telecom & Media": [
        ("{n} 5G subscriber base crosses 40 million, monetisation begins", 0.6),
        ("{n} ARPU rises to ₹185, marginal improvement QoQ", 0.45),
        ("{n} broadband subscriber additions at 2.1 million in Q3", 0.5),
        ("{n} spectrum debt repayment on track; leverage improves", 0.45),
        ("{n} OTT platform DAU growth of 31% outpaces peers", 0.55),
        ("{n} rural 4G rollout faces execution hurdles", -0.35),
        ("{n} enterprise fibre revenue growing at 25% CAGR", 0.5),
        ("{n} faces regulatory scrutiny on promotional tariff bundles", -0.4),
        ("{n} satellite broadband service launch in H2 FY26", 0.45),
        ("{n} churn rate at 1.1%, multi-quarter low", 0.45),
    ],
    "Consumer Discretionary": [
        ("{n} same-store sales growth of 14% beats industry trend", 0.6),
        ("{n} gross margin expansion on premiumisation push", 0.55),
        ("{n} online channel now accounts for 32% of total revenue", 0.5),
        ("{n} festive demand pulls forward Q3 vs Q4 revenue", 0.4),
        ("{n} new store openings target 80 outlets in FY26", 0.5),
        ("{n} faces elevated return rates on quick commerce channel", -0.35),
        ("{n} customer retention metrics hit new high post loyalty revamp", 0.55),
        ("{n} supply chain disruption impacts availability in key SKUs", -0.4),
        ("{n} private label mix rises to 22%, boosts gross margin", 0.5),
        ("{n} international expansion to GCC markets in FY26", 0.45),
    ],
    "Conglomerates": [
        ("{n} holding company discount narrows post strategic review", 0.5),
        ("{n} subsidiary IPO receives strong anchor investor interest", 0.6),
        ("{n} intra-group synergies deliver ₹800-Cr cost savings", 0.5),
        ("{n} demerger of key business unlocks shareholder value", 0.55),
        ("{n} group-level D/E at 0.6x, lowest in decade", 0.5),
        ("{n} capital allocation concerns raised by minority shareholders", -0.4),
        ("{n} new vertical expansion into green hydrogen segment", 0.45),
        ("{n} management succession plan removes key overhang", 0.4),
        ("{n} subsidiary faces regulatory probe in telecom division", -0.5),
        ("{n} promoter family resolves stake dispute through court settlement", 0.35),
    ],
}

_DEFAULT_TEMPLATES = [
    ("{n} reports quarterly results ahead of street expectations", 0.55),
    ("{n} management raises FY26 revenue guidance by 5%", 0.6),
    ("{n} secures multi-year strategic deal with marquee client", 0.55),
    ("{n} announces ₹500-Cr share buyback programme", 0.45),
    ("{n} analyst community turns cautious on valuation concerns", -0.35),
    ("{n} board approves capacity expansion with ₹1,200-Cr capex", 0.5),
    ("{n} promoter increases stake signalling long-term confidence", 0.4),
    ("{n} implements operational efficiency programme targeting 15% cost reduction", 0.5),
    ("{n} new product line receives strong initial market response", 0.55),
    ("{n} ESG report highlights progress on sustainability goals", 0.3),
    ("{n} Q3 EBITDA margin at 22.4%, beats consensus of 20.8%", 0.6),
    ("{n} faces competitive headwinds from new market entrant", -0.4),
]

_NSE_SOURCES = [
    "Economic Times", "Business Standard", "Mint", "Moneycontrol",
    "NDTV Profit", "Hindu BusinessLine", "Financial Express",
    "BloombergQuint", "Reuters India", "PTI Markets",
]


def get_mock_news_for_company(
    ticker: str,
    company_name: str,
    sector: str = "",
    n: int = 10,
) -> list[dict]:
    """
    Generate realistic-looking mock news articles for a specific company.
    Used as fallback when real APIs return no results.

    Args:
        ticker:       Stock symbol (e.g., 'TCS.NS')
        company_name: Full company name (e.g., 'Tata Consultancy Services')
        sector:       GICS-equivalent sector for contextual templates
        n:            Number of articles to generate  

    Returns:
        List of news dicts with standard {headline, source, timestamp, url} shape
    """
    rng = random.Random(ticker)  # deterministic seed so same ticker → same articles

    templates = _SECTOR_TEMPLATES.get(sector, []) + _DEFAULT_TEMPLATES
    rng.shuffle(templates)
    selected = templates[:n]

    short_name = company_name.split()[0]  # e.g. "Tata" from "Tata Consultancy..."

    now = datetime.now()
    articles = []
    for i, (tmpl, _score) in enumerate(selected):
        headline = tmpl.format(n=short_name)
        ts = now - timedelta(hours=rng.randint(1, 72))
        articles.append({
            "source":    rng.choice(_NSE_SOURCES),
            "headline":  headline,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "category":  "company",
            "ticker":    ticker,
            "url":       "",
            "_mock":     True,
        })
    return articles

    """Return a list of mock financial news headlines."""
    return [
        {
            "source": "Reuters",
            "headline": "Tech stocks surge as AI chip demand hits record highs",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Bloomberg",
            "headline": "Federal Reserve signals potential rate cuts in upcoming quarter",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "CNBC",
            "headline": "Apple reports record quarterly revenue beating analyst expectations",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "earnings",
        },
        {
            "source": "Financial Times",
            "headline": "Oil prices drop sharply amid global demand concerns",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "Wall Street Journal",
            "headline": "Semiconductor shortage eases as new fabs come online",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "MarketWatch",
            "headline": "Consumer confidence index rises to 18-month high",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "Reuters",
            "headline": "Tesla deliveries miss expectations amid increasing competition",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "automotive",
        },
        {
            "source": "Bloomberg",
            "headline": "Gold prices climb as investors seek safe-haven assets",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "CNBC",
            "headline": "Microsoft Azure revenue growth accelerates cloud dominance",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Financial Times",
            "headline": "Banking sector faces pressure from rising default rates",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "finance",
        },
    ]
