"""
Automatic service category detection based on provider name and business information
"""

import re

def detect_service_category(provider_name, business_address="", description="", specialties=""):
    """
    Automatically detect service category based on provider information
    
    Args:
        provider_name: Name of the business
        business_address: Business address (optional)
        description: Business description (optional)
        specialties: Business specialties (optional)
        
    Returns:
        str: Detected service category
    """
    # Combine all text for analysis
    text = f"{provider_name} {business_address} {description} {specialties}".lower()
    
    # Define category keywords with priority (more specific first)
    category_keywords = {
        "Electrical": [
            "electric", "electrical", "electrician", "wiring", "outlet", "circuit", "voltage",
            "panel", "breaker", "lighting", "fixture", "socket", "amperage", "conduit"
        ],
        "Plumbing": [
            "plumb", "plumbing", "plumber", "pipe", "drain", "toilet", "sink", "faucet",
            "leak", "water", "sewer", "septic", "bathroom", "kitchen", "tap", "valve"
        ],
        "HVAC": [
            "hvac", "heating", "cooling", "furnace", "air conditioning", "ac", "climate",
            "ventilation", "duct", "thermostat", "boiler", "heat pump", "refrigeration"
        ],
        "Roofing": [
            "roof", "roofing", "roofer", "shingle", "tile", "gutter", "eaves", "soffit",
            "flashing", "membrane", "slate", "metal roof", "skylight", "chimney"
        ],
        "Flooring": [
            "floor", "flooring", "hardwood", "laminate", "carpet", "tile", "vinyl",
            "bamboo", "cork", "stone", "marble", "granite", "ceramic", "installation"
        ],
        "Painting": [
            "paint", "painting", "painter", "interior", "exterior", "brush", "roller",
            "spray", "primer", "stain", "varnish", "coating", "drywall", "wallpaper"
        ],
        "Landscaping & Gardening": [
            "landscape", "landscaping", "garden", "gardening", "lawn", "grass", "sod",
            "irrigation", "sprinkler", "hedge", "plant", "flower", "mulch", "fertilizer"
        ],
        "Tree Services": [
            "tree", "trees", "arborist", "trimming", "pruning", "removal", "stump",
            "branch", "forestry", "timber", "wood", "logging", "chainsaw"
        ],
        "Cleaning Services": [
            "clean", "cleaning", "cleaner", "janitorial", "housekeeping", "maid",
            "sanitize", "disinfect", "vacuum", "mop", "dust", "wash", "scrub"
        ],
        "Pest Control": [
            "pest", "exterminator", "termite", "ant", "rodent", "mouse", "rat",
            "insect", "bug", "spray", "bait", "trap", "fumigation", "infestation"
        ],
        "Security Services": [
            "security", "alarm", "camera", "surveillance", "monitoring", "guard",
            "lock", "safe", "access control", "intercom", "cctv", "sensor"
        ],
        "Moving & Storage": [
            "moving", "mover", "storage", "packing", "unpacking", "relocation",
            "transport", "truck", "box", "warehouse", "container", "shipping"
        ],
        "Appliance Repair": [
            "appliance", "repair", "refrigerator", "washer", "dryer", "dishwasher",
            "oven", "stove", "microwave", "freezer", "garbage disposal", "range"
        ],
        "Carpet & Upholstery Cleaning": [
            "carpet cleaning", "upholstery", "steam clean", "shampoo", "fabric",
            "furniture cleaning", "rug cleaning", "spot removal", "stain removal"
        ],
        "Window Services": [
            "window", "glass", "glazing", "screen", "blind", "shutter", "curtain",
            "tinting", "replacement", "installation", "repair", "washing"
        ],
        "Masonry & Concrete": [
            "masonry", "concrete", "brick", "stone", "mortar", "cement", "foundation",
            "driveway", "patio", "walkway", "retaining wall", "fireplace"
        ],
        "Pool & Spa Services": [
            "pool", "spa", "hot tub", "jacuzzi", "swimming", "chlorine", "filter",
            "pump", "heater", "liner", "deck", "maintenance", "cleaning"
        ],
        "Garage Door Services": [
            "garage door", "overhead door", "opener", "spring", "track", "roller",
            "remote", "keypad", "sensor", "installation", "repair"
        ],
        "Locksmith Services": [
            "locksmith", "lock", "key", "deadbolt", "rekey", "duplicate", "safe",
            "combination", "emergency lockout", "door lock", "ignition"
        ],
        "Demolition": [
            "demolition", "demo", "tear down", "removal", "excavation", "debris",
            "concrete breaking", "structural removal", "site preparation"
        ],
        "Junk Removal": [
            "junk removal", "garbage", "trash", "waste", "disposal", "cleanup",
            "hauling", "debris removal", "clutter", "unwanted items"
        ],
        "Automotive Services": [
            "auto", "automotive", "car", "vehicle", "mechanic", "repair", "service",
            "oil change", "brake", "tire", "engine", "transmission", "battery"
        ],
        "IT & Tech Support": [
            "computer", "tech", "technology", "it", "software", "hardware", "network",
            "internet", "wifi", "data", "server", "troubleshoot", "support"
        ],
        "Photography": [
            "photo", "photography", "photographer", "picture", "image", "camera",
            "wedding", "portrait", "event", "studio", "shoot", "editing"
        ],
        "Catering": [
            "catering", "caterer", "food", "kitchen", "chef", "cooking", "meal",
            "restaurant", "banquet", "party", "event", "buffet", "menu"
        ],
        "Event Planning": [
            "event", "planning", "planner", "party", "wedding", "celebration",
            "coordination", "venue", "decoration", "entertainment", "organization"
        ]
    }
    
    # Score each category based on keyword matches
    category_scores = {}
    
    for category, keywords in category_keywords.items():
        score = 0
        for keyword in keywords:
            # Count occurrences of each keyword
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            score += count
            
            # Give extra weight to keywords in the business name
            if keyword in provider_name.lower():
                score += 2
        
        if score > 0:
            category_scores[category] = score
    
    # Return the category with the highest score
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        return best_category
    
    # Default fallback category
    return "General Maintenance & Repairs"

def get_category_suggestions(provider_name, business_address="", description="", specialties=""):
    """
    Get top 3 category suggestions with confidence scores
    
    Returns:
        list: List of tuples (category, confidence_score)
    """
    text = f"{provider_name} {business_address} {description} {specialties}".lower()
    
    category_keywords = {
        "Electrical": [
            "electric", "electrical", "electrician", "wiring", "outlet", "circuit", "voltage",
            "panel", "breaker", "lighting", "fixture", "socket", "amperage", "conduit"
        ],
        "Plumbing": [
            "plumb", "plumbing", "plumber", "pipe", "drain", "toilet", "sink", "faucet",
            "leak", "water", "sewer", "septic", "bathroom", "kitchen", "tap", "valve"
        ],
        "HVAC": [
            "hvac", "heating", "cooling", "furnace", "air conditioning", "ac", "climate",
            "ventilation", "duct", "thermostat", "boiler", "heat pump", "refrigeration"
        ],
        "Roofing": [
            "roof", "roofing", "roofer", "shingle", "tile", "gutter", "eaves", "soffit",
            "flashing", "membrane", "slate", "metal roof", "skylight", "chimney"
        ],
        "Flooring": [
            "floor", "flooring", "hardwood", "laminate", "carpet", "tile", "vinyl",
            "bamboo", "cork", "stone", "marble", "granite", "ceramic", "installation"
        ],
        "Painting": [
            "paint", "painting", "painter", "interior", "exterior", "brush", "roller",
            "spray", "primer", "stain", "varnish", "coating", "drywall", "wallpaper"
        ],
        "Landscaping & Gardening": [
            "landscape", "landscaping", "garden", "gardening", "lawn", "grass", "sod",
            "irrigation", "sprinkler", "hedge", "plant", "flower", "mulch", "fertilizer"
        ],
        "Tree Services": [
            "tree", "trees", "arborist", "trimming", "pruning", "removal", "stump",
            "branch", "forestry", "timber", "wood", "logging", "chainsaw"
        ],
        "Cleaning Services": [
            "clean", "cleaning", "cleaner", "janitorial", "housekeeping", "maid",
            "sanitize", "disinfect", "vacuum", "mop", "dust", "wash", "scrub"
        ],
        "General Maintenance & Repairs": [
            "maintenance", "repair", "handyman", "fix", "service", "general", "home",
            "property", "building", "construction", "renovation", "improvement"
        ]
    }
    
    category_scores = {}
    
    for category, keywords in category_keywords.items():
        score = 0
        for keyword in keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            score += count
            
            if keyword in provider_name.lower():
                score += 2
        
        if score > 0:
            category_scores[category] = score
    
    # Sort by score and return top 3
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_categories[:3] if sorted_categories else [("General Maintenance & Repairs", 1)]