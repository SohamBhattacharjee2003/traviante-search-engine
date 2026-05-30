"""Sample Traviante destination catalog.

This is the seed data used in two places:
  1. Mock mode — loaded into the in-memory metadata store so the stack runs locally.
  2. The indexing pipeline (``scripts/index_destinations.py``) — replace these entries
     with your real catalog, then run the script to embed + upsert them.

Images point at Unsplash (royalty-free) so the demo renders out of the box. In
production these would be Cloudinary URLs.
"""
from __future__ import annotations

from models.destination import Destination, TravelStyle

_U = "https://images.unsplash.com"

DESTINATIONS: list[Destination] = [
    Destination(
        id="bali-ubud",
        name="Ubud, Bali",
        country="Indonesia",
        tagline="Emerald rice terraces and jungle temples",
        description=(
            "Lush tropical rice terraces, sacred monkey forests and riverside spa "
            "retreats. A serene, green escape ideal for honeymoons and slow travel."
        ),
        images=[
            f"{_U}/photo-1537953773345-d172ccf13cf1?w=1200",
            f"{_U}/photo-1518548419970-58e3b4079ab2?w=1200",
        ],
        price_min_inr=90000,
        price_max_inr=250000,
        best_months=["april", "may", "june", "july", "september"],
        travel_styles=[TravelStyle.honeymoon, TravelStyle.cultural, TravelStyle.luxury],
        highlights=["Tegallalang rice terraces", "Private villa with pool", "Temple sunrise tour"],
    ),
    Destination(
        id="zermatt-switzerland",
        name="Zermatt",
        country="Switzerland",
        tagline="Snowy Alpine village beneath the Matterhorn",
        description=(
            "A car-free Alpine village wrapped in snow, framed by the iconic "
            "Matterhorn. Cosy chalets, glacier railways and world-class skiing."
        ),
        images=[
            f"{_U}/photo-1531366936337-7c912a4589a7?w=1200",
            f"{_U}/photo-1504280390367-361c6d9f38f4?w=1200",
        ],
        price_min_inr=350000,
        price_max_inr=900000,
        best_months=["december", "january", "february", "march"],
        travel_styles=[TravelStyle.honeymoon, TravelStyle.adventure, TravelStyle.luxury],
        highlights=["Matterhorn glacier paradise", "Gornergrat railway", "Ski-in chalet stay"],
    ),
    Destination(
        id="santorini-greece",
        name="Santorini",
        country="Greece",
        tagline="Whitewashed cliffs over the Aegean blue",
        description=(
            "Cliffside white villages with blue domes cascading toward a caldera sea. "
            "Famous sunsets, volcanic beaches and intimate cave hotels."
        ),
        images=[
            f"{_U}/photo-1570077188670-e3a8d69ac5ff?w=1200",
            f"{_U}/photo-1613395877344-13d4a8e0d49e?w=1200",
        ],
        price_min_inr=200000,
        price_max_inr=600000,
        best_months=["may", "june", "september", "october"],
        travel_styles=[TravelStyle.honeymoon, TravelStyle.beach, TravelStyle.luxury],
        highlights=["Oia caldera sunset", "Private catamaran cruise", "Cave suite with plunge pool"],
    ),
    Destination(
        id="kyoto-japan",
        name="Kyoto",
        country="Japan",
        tagline="Ancient temples and bamboo groves",
        description=(
            "Thousand-year-old temples, vermilion torii gates and tranquil bamboo "
            "forests. Cherry blossoms in spring, fiery maples in autumn."
        ),
        images=[
            f"{_U}/photo-1493976040374-85c8e12f0c0e?w=1200",
            f"{_U}/photo-1545569341-9eb8b30979d9?w=1200",
        ],
        price_min_inr=180000,
        price_max_inr=450000,
        best_months=["march", "april", "october", "november"],
        travel_styles=[TravelStyle.cultural, TravelStyle.family, TravelStyle.luxury],
        highlights=["Fushimi Inari shrine", "Arashiyama bamboo grove", "Traditional ryokan stay"],
    ),
    Destination(
        id="maldives-baa-atoll",
        name="Baa Atoll",
        country="Maldives",
        tagline="Overwater villas on turquoise lagoons",
        description=(
            "Private overwater bungalows above glassy turquoise lagoons, coral reefs "
            "teeming with manta rays. The definitive tropical beach honeymoon."
        ),
        images=[
            f"{_U}/photo-1514282401047-d79a71a590e8?w=1200",
            f"{_U}/photo-1439066615861-d1af74d74000?w=1200",
        ],
        price_min_inr=400000,
        price_max_inr=1200000,
        best_months=["november", "december", "january", "february", "march", "april"],
        travel_styles=[TravelStyle.honeymoon, TravelStyle.beach, TravelStyle.luxury],
        highlights=["Overwater villa", "Manta ray snorkelling", "Private sandbank dinner"],
    ),
    Destination(
        id="banff-canada",
        name="Banff",
        country="Canada",
        tagline="Turquoise glacial lakes and towering Rockies",
        description=(
            "Glacier-fed turquoise lakes mirrored beneath jagged Rocky Mountain peaks. "
            "Hiking and canoeing in summer, powder skiing in winter."
        ),
        images=[
            f"{_U}/photo-1561134643-668f9057cce4?w=1200",
            f"{_U}/photo-1609825488888-3a766db05542?w=1200",
        ],
        price_min_inr=250000,
        price_max_inr=550000,
        best_months=["june", "july", "august", "september"],
        travel_styles=[TravelStyle.adventure, TravelStyle.family],
        highlights=["Lake Louise canoeing", "Icefields Parkway drive", "Banff Gondola summit"],
    ),
    Destination(
        id="marrakech-morocco",
        name="Marrakech",
        country="Morocco",
        tagline="Riads, souks and Saharan colour",
        description=(
            "Labyrinthine souks, jewel-toned riads and rooftop sunsets over the Atlas "
            "Mountains. A vivid, sensory cultural adventure."
        ),
        images=[
            f"{_U}/photo-1597212618440-806262de4f6b?w=1200",
            f"{_U}/photo-1539020140153-e479b8c22e70?w=1200",
        ],
        price_min_inr=120000,
        price_max_inr=350000,
        best_months=["march", "april", "october", "november"],
        travel_styles=[TravelStyle.cultural, TravelStyle.adventure],
        highlights=["Jemaa el-Fnaa night market", "Luxury riad stay", "Atlas Mountains day trip"],
    ),
    Destination(
        id="queenstown-nz",
        name="Queenstown",
        country="New Zealand",
        tagline="Adventure capital by a mountain lake",
        description=(
            "Adrenaline central on the shores of Lake Wakatipu — bungee, jet boats and "
            "alpine hikes, ringed by the dramatic Remarkables range."
        ),
        images=[
            f"{_U}/photo-1589802829985-817e51171b92?w=1200",
            f"{_U}/photo-1469854523086-cc02fe5d8800?w=1200",
        ],
        price_min_inr=300000,
        price_max_inr=650000,
        best_months=["december", "january", "february", "march"],
        travel_styles=[TravelStyle.adventure, TravelStyle.family],
        highlights=["Bungee at Kawarau Bridge", "Milford Sound cruise", "Skyline gondola luge"],
    ),
]
