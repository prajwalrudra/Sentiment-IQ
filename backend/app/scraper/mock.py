"""
SentimentIQ — Mock Review Generator

Generates high-fidelity, realistic product reviews for demo and fallback.
Reviews match the product category and include varied sentiments, ratings, and writing styles.
"""

import random
from typing import List, Dict, Tuple
from urllib.parse import urlparse
from datetime import datetime, timedelta


# ── Review Templates by Category ─────────────────────────────

REVIEWS_DB = {
    "headphones": {
        "product_name": "ProSound X500 Noise-Cancelling Headphones",
        "reviews": [
            {"text": "Absolutely love these headphones! The noise cancellation is top-notch and the sound quality is incredibly rich and detailed. Bass is punchy without being overwhelming. Best purchase I've made this year.", "rating": 5, "sentiment": "positive"},
            {"text": "The audio quality is decent for the price range, but the noise cancelling could be better. It doesn't completely block out loud environments like trains or busy cafes. Comfortable to wear though.", "rating": 3, "sentiment": "neutral"},
            {"text": "Battery life is phenomenal - I'm getting close to 35 hours on a single charge. The carrying case is also premium quality. Bluetooth connectivity is seamless with my phone and laptop.", "rating": 5, "sentiment": "positive"},
            {"text": "Terrible build quality. The headband started cracking after just 2 months of regular use. For this price, I expected much better durability. Very disappointing.", "rating": 1, "sentiment": "negative"},
            {"text": "Sound is crystal clear for music and calls. The microphone quality during video calls is surprisingly good. My colleagues said I sound much clearer than with my previous headset.", "rating": 4, "sentiment": "positive"},
            {"text": "The ear cushions are super soft and comfortable even during long sessions. I wear them for 6-8 hours while working and no discomfort at all. Great ergonomic design.", "rating": 5, "sentiment": "positive"},
            {"text": "Returned these immediately. The left ear cup had a buzzing sound at higher volumes. Quality control seems to be an issue. Customer support was unhelpful.", "rating": 1, "sentiment": "negative"},
            {"text": "Good headphones overall. The touch controls on the ear cup are intuitive once you get used to them. Wish the app had more equalizer presets though.", "rating": 4, "sentiment": "positive"},
            {"text": "The ANC is average compared to Sony WH-1000XM5 or Bose 700. Sound quality is good but not audiophile-level. Works fine for casual listening and commuting.", "rating": 3, "sentiment": "neutral"},
            {"text": "Overpriced for what you get. The sound is muddy in the mid-range and the Bluetooth connection drops occasionally. There are better options available for half the price.", "rating": 2, "sentiment": "negative"},
            {"text": "Multipoint connection works perfectly! I can switch between my phone and laptop seamlessly. The folding design makes them very portable for travel.", "rating": 5, "sentiment": "positive"},
            {"text": "After using these for 6 months, the padding on the headband is peeling. Sound quality is still great but the build quality doesn't justify the premium price tag.", "rating": 2, "sentiment": "negative"},
            {"text": "Received these as a gift and was blown away. The unboxing experience is premium, the sound signature is warm and engaging. Perfect for jazz and classical music.", "rating": 5, "sentiment": "positive"},
            {"text": "The noise cancellation makes a weird whistling noise on flights. Fine for office use but not great for air travel. Audio quality is otherwise quite good.", "rating": 3, "sentiment": "neutral"},
            {"text": "Fast charging is a game changer - 10 minutes gives 5 hours of playback. The weight is perfectly balanced and they don't feel heavy even on long flights. Highly recommend!", "rating": 5, "sentiment": "positive"},
        ],
    },
    "smartwatch": {
        "product_name": "FitTrack Ultra Smartwatch",
        "reviews": [
            {"text": "This smartwatch has completely transformed my fitness routine! The heart rate monitoring is incredibly accurate and the sleep tracking gives amazing insights. The AMOLED display is gorgeous.", "rating": 5, "sentiment": "positive"},
            {"text": "Battery life is disappointing - only lasts about 2 days with normal use. I expected at least 5 days. The fitness tracking features are decent though.", "rating": 2, "sentiment": "negative"},
            {"text": "The GPS tracking is spot-on during runs. Maps out my route perfectly and the pace alerts are very helpful for training. Step counter is also accurate.", "rating": 4, "sentiment": "positive"},
            {"text": "Looks premium on the wrist. The stainless steel case and sapphire glass give it a luxury feel. Gets lots of compliments. The interchangeable bands are a nice touch.", "rating": 5, "sentiment": "positive"},
            {"text": "App ecosystem is limited compared to Apple Watch or Galaxy Watch. Many popular apps are not available. The proprietary OS feels restrictive.", "rating": 2, "sentiment": "negative"},
            {"text": "Water resistance works as advertised - I swim with it regularly. The swim tracking mode is basic but functional. Wish it could track different stroke types.", "rating": 4, "sentiment": "positive"},
            {"text": "The notification system is buggy. Messages sometimes appear hours late or not at all. Had to reset the watch multiple times. Needs a firmware update badly.", "rating": 1, "sentiment": "negative"},
            {"text": "SpO2 monitoring and stress tracking are great additions. The guided breathing exercises have genuinely helped me manage anxiety. Very thoughtful features.", "rating": 5, "sentiment": "positive"},
            {"text": "The touchscreen responsiveness is mediocre. Sometimes need to tap multiple times for it to register. Frustrating when trying to check notifications quickly.", "rating": 2, "sentiment": "negative"},
            {"text": "Excellent value for money. Offers 90% of what premium smartwatches do at less than half the price. The workout detection is surprisingly accurate.", "rating": 4, "sentiment": "positive"},
            {"text": "Comfortable to wear all day and night. Lightweight design and soft silicone band don't irritate my sensitive skin. The always-on display option is nice.", "rating": 4, "sentiment": "positive"},
            {"text": "Music controls and call management work seamlessly. The built-in speaker for calls is clear enough for quick conversations. Very convenient feature.", "rating": 4, "sentiment": "positive"},
        ],
    },
    "laptop": {
        "product_name": "ThinBook Pro 14\" Laptop",
        "reviews": [
            {"text": "Blazing fast performance! The latest processor handles everything I throw at it - from coding in multiple IDEs to running Docker containers. 16GB RAM is perfect for development.", "rating": 5, "sentiment": "positive"},
            {"text": "The display is absolutely stunning - sharp, vibrant colors with excellent brightness. The anti-glare coating works well outdoors. Great for photo editing and design work.", "rating": 5, "sentiment": "positive"},
            {"text": "Keyboard is terrible. The key travel is way too shallow and typing for long periods causes finger fatigue. Coming from a ThinkPad, this is a major downgrade.", "rating": 2, "sentiment": "negative"},
            {"text": "Fan noise under load is very noticeable. During video calls with screen sharing, the fans ramp up and colleagues can hear it. Needs better thermal management.", "rating": 2, "sentiment": "negative"},
            {"text": "Battery easily lasts 10+ hours for regular office work. I can go a full workday without charging. The USB-C charging is super convenient.", "rating": 5, "sentiment": "positive"},
            {"text": "Lightweight and portable - perfect for my daily commute. The build quality is solid with an all-aluminum chassis. Feels premium and durable.", "rating": 4, "sentiment": "positive"},
            {"text": "Only 2 USB-C ports and no USB-A is a deal breaker. I need to carry a dongle everywhere. They should have included at least one USB-A port.", "rating": 2, "sentiment": "negative"},
            {"text": "The webcam quality is surprisingly good for a laptop - 1080p with decent low-light performance. Windows Hello face unlock is fast and reliable.", "rating": 4, "sentiment": "positive"},
            {"text": "Runs hot under sustained workload. The bottom gets uncomfortable on the lap. Fine on a desk but not ideal for actual 'laptop' use.", "rating": 3, "sentiment": "neutral"},
            {"text": "Software bloatware was annoying. Took me 30 minutes to uninstall all the preloaded junk. Why do manufacturers still do this? Clean install fixed everything.", "rating": 3, "sentiment": "neutral"},
        ],
    },
    "skincare": {
        "product_name": "GlowUp Vitamin C Serum",
        "reviews": [
            {"text": "After 4 weeks of daily use, my skin is visibly brighter and more even-toned. Dark spots from sun damage have faded noticeably. My dermatologist was impressed with the results!", "rating": 5, "sentiment": "positive"},
            {"text": "Caused terrible breakouts on my sensitive skin. My face was red and irritated for days after using it. Should come with a stronger warning about patch testing.", "rating": 1, "sentiment": "negative"},
            {"text": "The texture is lightweight and absorbs quickly without leaving any sticky residue. Works well under makeup and sunscreen. A little goes a long way - the bottle will last months.", "rating": 5, "sentiment": "positive"},
            {"text": "Decent serum but nothing revolutionary. I've tried better vitamin C products at a similar price point. The packaging could be improved to prevent oxidation.", "rating": 3, "sentiment": "neutral"},
            {"text": "Absolutely love the results! My fine lines around the eyes are less visible and my skin has a natural glow. Getting compliments from friends and family. Will definitely repurchase.", "rating": 5, "sentiment": "positive"},
            {"text": "The product oxidized within 3 weeks of opening - turned dark orange. Vitamin C serums should be in opaque bottles. Wasted my money.", "rating": 1, "sentiment": "negative"},
            {"text": "Good concentration of Vitamin C (20%) with added hyaluronic acid and vitamin E. The formulation is science-backed. Slight tingling on first use is normal and goes away.", "rating": 4, "sentiment": "positive"},
            {"text": "Smells slightly metallic which is off-putting. The scent goes away after application but it's not pleasant during the routine. Results are okay though.", "rating": 3, "sentiment": "neutral"},
        ],
    },
    "coffee": {
        "product_name": "BeanMaster Premium Dark Roast Coffee",
        "reviews": [
            {"text": "Rich, bold flavor with hints of dark chocolate and caramel. Smooth finish with no bitterness. This has become my go-to morning coffee. The aroma alone is heavenly.", "rating": 5, "sentiment": "positive"},
            {"text": "Way too bitter for my taste. Even with cream and sugar, the bitterness is overpowering. If you prefer light or medium roast, this is not for you.", "rating": 2, "sentiment": "negative"},
            {"text": "The beans arrive freshly roasted and the packaging keeps them fresh. I can taste the difference compared to supermarket brands. Worth every penny.", "rating": 5, "sentiment": "positive"},
            {"text": "Makes excellent espresso. The crema is thick and the flavor is complex. Also works great in a French press. Very versatile coffee beans.", "rating": 5, "sentiment": "positive"},
            {"text": "Received stale beans. The roast date was over 3 months ago. For a 'premium' coffee, I expected freshly roasted beans. Very disappointed with the quality control.", "rating": 1, "sentiment": "negative"},
            {"text": "Good coffee but overpriced. You can find similar quality from local roasters at half the cost. The subscription service is convenient though.", "rating": 3, "sentiment": "neutral"},
            {"text": "Perfect for cold brew! The dark roast flavor really shines when brewed cold. Smooth, rich, and refreshing. I make a big batch every weekend.", "rating": 5, "sentiment": "positive"},
            {"text": "The single-origin Ethiopian beans are exceptional. Notes of blueberry and jasmine come through beautifully in a pour-over. One of the best specialty coffees I've tried.", "rating": 5, "sentiment": "positive"},
        ],
    },
    "software": {
        "product_name": "TaskFlow Project Management Software",
        "reviews": [
            {"text": "TaskFlow has revolutionized our team's workflow! The Kanban boards are intuitive, the Gantt charts are powerful, and the real-time collaboration features save us hours every week. Best PM tool we've used.", "rating": 5, "sentiment": "positive"},
            {"text": "The learning curve is steep. Took our team almost a month to get comfortable with all the features. Documentation is lacking and the UI is cluttered with options.", "rating": 2, "sentiment": "negative"},
            {"text": "Integration with Slack, GitHub, and Google Workspace works perfectly. Notifications are timely and the automated workflows have eliminated so many manual tasks.", "rating": 5, "sentiment": "positive"},
            {"text": "Pricing is unreasonable for small teams. The free tier is too limited and the pro plan is expensive per user. Smaller competitors offer better value.", "rating": 2, "sentiment": "negative"},
            {"text": "The mobile app is surprisingly functional. I can manage tasks, review updates, and approve requests on the go. The offline mode is a great addition.", "rating": 4, "sentiment": "positive"},
            {"text": "Customer support is excellent. They resolved a critical data migration issue within 2 hours. The dedicated account manager has been very helpful during onboarding.", "rating": 5, "sentiment": "positive"},
            {"text": "Frequent downtime issues over the past month. We experienced 3 outages during business hours which disrupted our sprint planning. Reliability needs improvement.", "rating": 1, "sentiment": "negative"},
            {"text": "The reporting and analytics dashboard is comprehensive. Burndown charts, velocity tracking, and resource allocation views help us make data-driven decisions. Love the custom report builder.", "rating": 5, "sentiment": "positive"},
            {"text": "API is well-documented and powerful. We built custom integrations with our internal tools easily. The webhook system is flexible and reliable.", "rating": 4, "sentiment": "positive"},
            {"text": "The time tracking feature is basic compared to dedicated tools like Toggl or Harvest. It works for simple tracking but lacks detailed reporting and invoice generation.", "rating": 3, "sentiment": "neutral"},
        ],
    },
}

# ── Fallback generic reviews ─────────────────────────────────
GENERIC_REVIEWS = [
    {"text": "Great product! Exactly what I was looking for. Quality is excellent and delivery was fast. Would definitely recommend to others.", "rating": 5, "sentiment": "positive"},
    {"text": "Decent product for the price. Does what it's supposed to do. Nothing extraordinary but no complaints either. Average experience overall.", "rating": 3, "sentiment": "neutral"},
    {"text": "Very disappointed with this purchase. The product looks nothing like the photos and the quality is cheap. Requesting a refund.", "rating": 1, "sentiment": "negative"},
    {"text": "Exceeded my expectations! The build quality is premium and it works flawlessly. Customer service was also very responsive when I had questions.", "rating": 5, "sentiment": "positive"},
    {"text": "Product arrived damaged. The packaging was inadequate for shipping. Replacement process was slow and frustrating.", "rating": 1, "sentiment": "negative"},
    {"text": "Good value for money. Not the best in its category but definitely solid for the price point. Happy with my purchase.", "rating": 4, "sentiment": "positive"},
    {"text": "The product is okay but the user manual is confusing and incomplete. Took a while to figure things out. Could use better documentation.", "rating": 3, "sentiment": "neutral"},
    {"text": "Absolutely love it! Using it daily and it has made a real difference. Highly recommend to anyone considering this purchase.", "rating": 5, "sentiment": "positive"},
    {"text": "Stopped working after 2 weeks. Very poor reliability. Customer support told me the warranty doesn't cover this issue. Never buying from this brand again.", "rating": 1, "sentiment": "negative"},
    {"text": "Solid product with great features. Easy to set up and use. The only minor issue is the size is slightly bigger than I expected.", "rating": 4, "sentiment": "positive"},
    {"text": "Perfect for my needs. Clean design, easy to use, and performs consistently. The attention to detail in the packaging was also impressive.", "rating": 5, "sentiment": "positive"},
    {"text": "Mediocre at best. There are better alternatives available. The marketing overpromises and the actual product underdelivers.", "rating": 2, "sentiment": "negative"},
]


def _random_names() -> List[str]:
    """Generate a list of random reviewer names."""
    first_names = [
        "Amit", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Divya",
        "Arjun", "Meera", "Karthik", "Pooja", "Nikhil", "Riya", "Sanjay", "Neha",
        "James", "Sarah", "Michael", "Emma", "David", "Olivia", "Robert", "Sophia",
        "Alex", "Maya", "Chris", "Zara", "Daniel", "Lily", "Raj", "Aisha",
    ]
    last_initials = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [f"{random.choice(first_names)} {random.choice(last_initials)}." for _ in range(50)]


def _random_dates(count: int) -> List[str]:
    """Generate random dates within the last 6 months."""
    dates = []
    now = datetime.now()
    for _ in range(count):
        days_ago = random.randint(1, 180)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%B %d, %Y"))
    return dates


def generate_mock_reviews(url: str) -> Tuple[str, List[Dict]]:
    """
    Generate realistic mock reviews based on the URL or product category.

    Args:
        url: Product URL or preset identifier

    Returns:
        Tuple of (product_name, list of review dicts)
    """
    url_lower = url.lower()

    # Try to match a known category
    matched_category = None
    for category in REVIEWS_DB:
        if category in url_lower:
            matched_category = category
            break

    if matched_category:
        data = REVIEWS_DB[matched_category]
        product_name = data["product_name"]
        base_reviews = data["reviews"]
    else:
        product_name = "Product"
        # Try to extract a product name from the URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            product_name = path_parts[-1].replace("-", " ").replace("_", " ").title()
        base_reviews = GENERIC_REVIEWS

    # Generate reviewer names and dates
    names = _random_names()
    dates = _random_dates(len(base_reviews))

    reviews = []
    for i, review_data in enumerate(base_reviews):
        reviews.append({
            "text": review_data["text"],
            "rating": review_data.get("rating", random.randint(1, 5)),
            "reviewer_name": names[i % len(names)],
            "date": dates[i],
            "verified_purchase": random.random() > 0.3,
        })

    # Shuffle for variety
    random.shuffle(reviews)

    return product_name, reviews
