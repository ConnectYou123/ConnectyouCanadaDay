"""
AI Agent Service for ConnectYou - Intelligent Provider Matching System
Uses Claude API to understand user needs and connect them with the right providers
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from models import ServiceProviderReport, ServiceProvider
from twilio_service import send_sms
from app import db
from config import ai_config

# API URLs for different providers
API_URLS = {
    'claude': "https://api.anthropic.com/v1/messages",
    'openai': "https://api.openai.com/v1/chat/completions",
    'google': "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
}

class AIAgentService:
    def __init__(self):
        self.conversation_memory = {}  # Store conversation context
        
    def get_ai_response(self, messages: List[Dict], system_prompt: str = "") -> str:
        """
        Get response from configured AI provider (Claude, OpenAI, or Google)
        """
        provider = ai_config.get('AI_PROVIDER', 'claude')
        api_key = ai_config.get_api_key(provider)
        
        if not api_key:
            return f"I apologize, but the {provider} AI service is not configured. Please check your API key settings."
        
        try:
            if provider == 'claude':
                return self._get_claude_response(messages, system_prompt, api_key)
            elif provider == 'openai':
                return self._get_openai_response(messages, system_prompt, api_key)
            elif provider == 'google':
                return self._get_google_response(messages, system_prompt, api_key)
            else:
                return "Unsupported AI provider configured."
                
        except Exception as e:
            logging.error(f"{provider} API error: {str(e)}")
            return "I'm having trouble processing your request right now. Please try again later."
    
    def _get_claude_response(self, messages: List[Dict], system_prompt: str, api_key: str) -> str:
        """Get response from Claude API"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": ai_config.get('AI_MODEL', 'claude-3-sonnet-20240229'),
            "max_tokens": ai_config.get('MAX_TOKENS', 1024),
            "messages": messages
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        response = requests.post(API_URLS['claude'], headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["content"][0]["text"]
    
    def _get_openai_response(self, messages: List[Dict], system_prompt: str, api_key: str) -> str:
        """Get response from OpenAI API using the official client"""
        try:
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Convert messages format for OpenAI
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get the model from config, default to gpt-3.5-turbo
            model = ai_config.get('AI_MODEL', 'gpt-3.5-turbo')
            
            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=int(ai_config.get('MAX_TOKENS', 1024)),
                temperature=float(ai_config.get('TEMPERATURE', 0.7)),
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            # Fallback to requests method if client fails
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            data = {
                "model": ai_config.get('AI_MODEL', 'gpt-3.5-turbo'),
                "messages": openai_messages,
                "max_tokens": ai_config.get('MAX_TOKENS', 1024),
                "temperature": ai_config.get('TEMPERATURE', 0.7)
            }
            
            response = requests.post(API_URLS['openai'], headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _get_google_response(self, messages: List[Dict], system_prompt: str, api_key: str) -> str:
        """Get response from Google Gemini API"""
        # Combine system prompt and messages for Google format
        full_prompt = ""
        if system_prompt:
            full_prompt += f"System: {system_prompt}\n\n"
        
        for msg in messages:
            role = "Human" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
        
        full_prompt += "Assistant:"
        
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": ai_config.get('MAX_TOKENS', 1024),
                "temperature": ai_config.get('TEMPERATURE', 0.7)
            }
        }
        
        url = f"{API_URLS['google']}?key={api_key}"
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    
    def _simple_extract(self, text: str) -> Dict:
        """Very robust local extractor that identifies service and urgency without LLM.
        Handles common phrasings and prevents repetitive fallback.
        """
        t = (text or "").lower()
        categories = {
            'electrician': ['electric', 'outlet', 'switch', 'breaker', 'panel', 'wiring', 'light'],
            'plumber': ['plumb', 'leak', 'pipe', 'toilet', 'sink', 'drain', 'faucet', 'water heater'],
            'hvac': ['hvac', 'furnace', 'air condition', 'ac ', 'heating', 'cooling'],
            'general handyman': ['handyman', 'mount', 'repair', 'install', 'fix'],
            'house cleaner': ['clean', 'cleaner', 'housekeep'],
            'painter': ['paint', 'painting'],
            'roofing specialist': ['roof', 'shingle', 'leak roof'],
            'appliance repair technician': ['fridge', 'washer', 'dryer', 'dishwasher', 'appliance'],
        }
        service = None
        for cat, keys in categories.items():
            if any(k in t for k in keys):
                service = cat.title()
                break
        urgency = 'high' if any(k in t for k in ['urgent', 'asap', 'emergency', 'right now', 'no power', 'flood']) else 'medium'
        return {
            'service_category': service,
            'urgency': urgency,
        }

    def analyze_user_request(self, user_message: str, conversation_id: str, city: str) -> Dict:
        """
        Analyze user request and determine next steps
        """
        system_prompt = f"""You are an intelligent and friendly AI assistant for ConnectYou, a trusted service provider platform serving {city}. 
        Your role is to help users quickly find the right professional service providers for their home and business needs.
        You also have FULL ACCESS to the ConnectYou admin panel and can perform administrative tasks.

        PERSONALITY: Be helpful, professional, conversational, and solution-focused. Show genuine care for their situation and respond with warmth while being efficient.

        Available service categories:
        - Electrician (electrical repairs, installations, upgrades)
        - Plumber (plumbing repairs, installations, water heaters)
        - HVAC (heating, ventilation, air conditioning)
        - General Handyman (repairs, installations, maintenance)
        - House Cleaner (residential cleaning services)
        - Carpenter (woodwork, custom builds, repairs)
        - Painter (interior/exterior painting)
        - Roofing Specialist (roof repairs, installations)
        - Appliance Repair Technician (home appliance fixes)
        - Locksmith (lock services, security)
        - Pest Control (pest management, extermination)
        - Moving Services (relocation assistance)
        - Lawn Care Specialist (landscaping, maintenance)
        - Tree Service Technician (tree care, removal)
        - Masonry (stonework, brickwork)
        - Flooring (floor installation, repairs)
        - Window Cleaner
        - Garage Door Technician
        - Fence & Gate Installer
        - Chimney Sweep
        - Junk Removal Specialist
        - Gutter Cleaning Specialist
        - Smart Home Technician
        - Pool Maintenance Technician
        - Mold Remediation Specialist

        ADMIN PANEL ACCESS - You have access to the following admin tools via the Agent Admin API:
        1. **Provider Management**: List, search, add, edit, and delete service providers
        2. **City Management**: List, add, edit, and delete cities on the platform
        3. **Category Management**: List, add, edit, and delete service categories
        4. **Advertisement Management**: List, create, edit, and delete advertisements
        5. **Customer Interaction Logs**: View, create, and manage interaction logs
        6. **Chat Conversations**: View conversations, reply to users, update status/priority
        7. **Dashboard Analytics**: View platform-wide stats (providers, cities, chats, reports)
        8. **Email Logs**: View sent email history
        9. **Provider Reports**: View and manage user-submitted provider feedback/reports
        10. **Waiting List**: View and manage service provider applications

        All admin endpoints are at /agent-api/* and require Bearer token authentication.

        INSTRUCTIONS:
        1. Understand what service the user needs from their message
        2. Assess the urgency level (emergency = high, soon = medium, flexible = low)
        3. Determine if you have enough info to connect them with providers
        4. If the user asks about admin tasks, use your admin panel access to help
        5. Respond conversationally and helpfully

        RESPONSE FORMAT - Always respond with valid JSON only:
        {{
          "response_text": "Your friendly, helpful response to the user",
          "needs_more_info": true/false,
          "service_category": "Exact category name from the list above",
          "urgency": "low/medium/high",
          "details_collected": {{"key": "value"}},
          "ready_to_contact": true/false,
          "follow_up_questions": ["specific question if needed"],
          "admin_action": null or {{"tool": "tool_name", "params": {{}}}}
        }}

        KEY DETAILS TO GATHER:
        - Specific problem description
        - Timeline/urgency
        - User's name and phone number
        - Location details if needed
        - Any special requirements

        EXAMPLES:
        User: "My toilet is leaking water everywhere!"
        Response: {{"response_text": "Oh no! A leaking toilet can cause water damage quickly. I can connect you with emergency plumbers in {city} right away. What's your name and phone number so they can contact you immediately?", "needs_more_info": true, "service_category": "Plumber", "urgency": "high", "ready_to_contact": false, "follow_up_questions": ["What's your name and phone number?"], "admin_action": null}}

        User: "I need someone to paint my living room next month"
        Response: {{"response_text": "I'd love to help you find a great painter for your living room! What's the size of the room, and do you have any color preferences? Also, what's your name and phone number so painters can provide quotes?", "needs_more_info": true, "service_category": "Painter", "urgency": "low", "ready_to_contact": false, "follow_up_questions": ["Room size and color preferences?", "Your name and phone number?"], "admin_action": null}}

        User: "Can you access the admin panel?"
        Response: {{"response_text": "Yes! I have full access to the ConnectYou admin panel. I can manage providers, cities, categories, advertisements, chat conversations, interaction logs, view analytics, email logs, reports, and the waiting list. What would you like me to do?", "needs_more_info": false, "service_category": null, "urgency": "low", "ready_to_contact": false, "follow_up_questions": [], "admin_action": null}}

        Remember: Be warm, efficient, and solution-focused. Always respond in valid JSON format."""

        # Get conversation history
        conversation_history = self.conversation_memory.get(conversation_id, [])
        
        # Add current message to conversation
        messages = conversation_history + [{"role": "user", "content": user_message}]
        
        response = self.get_ai_response(messages, system_prompt)
        
        try:
            # Parse JSON response
            analysis = json.loads(response)
            
            # Update conversation memory
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": analysis.get("response_text", "")})
            self.conversation_memory[conversation_id] = conversation_history[-10:]  # Keep last 10 messages
            
            return analysis
            
        except json.JSONDecodeError:
            # Strong local fallback to avoid repetitive responses
            logging.warning("Claude JSON parse failed; using rule-based extraction fallback")
            extracted = self._simple_extract(user_message)
            service = extracted.get('service_category')
            urgency = extracted.get('urgency', 'medium')
            if service:
                return {
                    "response_text": f"Got it — you need a {service.lower()}. I can help with that. Do you want me to contact a few top-rated {service.lower()} providers in {city}? Please share your name and phone number so they can reach you.",
                    "needs_more_info": False,
                    "service_category": service,
                    "urgency": urgency,
                    "details_collected": {"problem_description": user_message},
                    "ready_to_contact": False,
                    "follow_up_questions": ["What is the best phone number to reach you?", "Any specific timing or preferences?"]
                }
            else:
                return {
                    "response_text": "Thanks! To connect you with the right pro, which service do you need (e.g., Electrician, Plumber, Handyman)?",
                    "needs_more_info": True,
                    "service_category": None,
                    "urgency": urgency,
                    "details_collected": {},
                    "ready_to_contact": False,
                    "follow_up_questions": ["Which service do you need?", "How urgent is it?"]
                }
    
    def get_matching_providers(self, service_category: str, city: str, limit: int = 5) -> List[Dict]:
        """
        Get matching providers for the service category
        """
        providers = []
        
        try:
            # First try ServiceProvider table (active providers)
            service_providers = ServiceProvider.query.filter(
                ServiceProvider.service_category.ilike(f"%{service_category}%"),
                ServiceProvider.city.ilike(f"%{city}%"),
                ServiceProvider.status == 'active'
            ).limit(limit).all()
            
            for provider in service_providers:
                providers.append({
                    'name': provider.name,
                    'phone': provider.phone,
                    'email': provider.email,
                    'rating': provider.star_rating or 4.5,
                    'review_count': provider.review_count or 0,
                    'address': provider.business_address,
                    'city': provider.city,
                    'service_category': provider.service_category,
                    'description': provider.description,
                    'source': 'active_provider'
                })
            
            # If we need more providers, check ServiceProviderReport (approved applications)
            if len(providers) < limit:
                remaining_limit = limit - len(providers)
                
                reports = ServiceProviderReport.query.filter(
                    ServiceProviderReport.service_category.ilike(f"%{service_category}%"),
                    ServiceProviderReport.city.ilike(f"%{city}%"),
                    ServiceProviderReport.report_reason == 'service_provider_application',
                    ServiceProviderReport.status == 'approved'
                ).limit(remaining_limit).all()
                
                for report in reports:
                    report_info = json.loads(report.report_data)
                    providers.append({
                        'name': report_info.get('business_name', 'Unknown'),
                        'phone': report_info.get('business_phone', ''),
                        'email': report_info.get('primary_email', ''),
                        'rating': float(report_info.get('rating', 4.5)),
                        'review_count': int(report_info.get('review_count', 0)),
                        'address': report_info.get('business_address', ''),
                        'city': report_info.get('city', ''),
                        'service_category': report_info.get('service_category', ''),
                        'description': f"Professional {service_category} service provider",
                        'source': 'approved_application'
                    })
            
            # Sort by rating and review count
            providers.sort(key=lambda x: (x['rating'], x['review_count']), reverse=True)
            
            return providers[:limit]
            
        except Exception as e:
            logging.error(f"Error getting matching providers: {str(e)}")
            return []
    
    def create_provider_message(self, user_details: Dict, analysis: Dict) -> str:
        """
        Create a professional message to send to providers
        """
        service_category = analysis.get('service_category', 'service')
        urgency = analysis.get('urgency', 'medium')
        details = analysis.get('details_collected', {})
        
        urgency_text = {
            'high': '🚨 URGENT REQUEST',
            'medium': '⏰ Service Request', 
            'low': '📝 Service Inquiry'
        }.get(urgency, '📝 Service Request')
        
        message = f"{urgency_text}\n\n"
        message += f"New {service_category} request from ConnectYou:\n\n"
        
        # Add user contact info
        if user_details.get('name'):
            message += f"Customer: {user_details['name']}\n"
        if user_details.get('phone'):
            message += f"Phone: {user_details['phone']}\n"
        if user_details.get('email'):
            message += f"Email: {user_details['email']}\n"
        
        message += f"\nService Needed: {service_category}\n"
        
        # Add specific details if available
        if details.get('problem_description'):
            message += f"Details: {details['problem_description']}\n"
        
        if details.get('budget_range'):
            message += f"Budget: {details['budget_range']}\n"
            
        if details.get('preferred_time'):
            message += f"Preferred Time: {details['preferred_time']}\n"
        
        if urgency == 'high':
            message += f"\n⚠️ This is marked as urgent - please respond ASAP"
        
        message += f"\n\nTo respond, please call or text the customer directly."
        message += f"\n\nThis lead was generated by ConnectYou AI Assistant at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def send_to_providers(self, providers: List[Dict], message: str, user_details: Dict, analysis: Dict) -> Dict:
        """
        Send SMS to selected providers
        """
        results = {
            'sent_count': 0,
            'failed_count': 0,
            'sent_to': [],
            'errors': []
        }
        
        for provider in providers:
            try:
                phone = provider.get('phone', '').strip()
                if not phone:
                    results['failed_count'] += 1
                    results['errors'].append(f"No phone number for {provider.get('name', 'Unknown')}")
                    continue
                
                # Send SMS
                message_sid = send_sms(phone, message)
                
                if message_sid:
                    results['sent_count'] += 1
                    results['sent_to'].append({
                        'name': provider.get('name'),
                        'phone': phone,
                        'message_sid': message_sid
                    })
                    
                    logging.info(f"AI Agent sent lead to {provider.get('name')} at {phone}")
                else:
                    results['failed_count'] += 1
                    results['errors'].append(f"Failed to send SMS to {provider.get('name')}")
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append(f"Error sending to {provider.get('name', 'Unknown')}: {str(e)}")
                logging.error(f"Error sending SMS to provider: {str(e)}")
        
        return results
    
    def process_user_message(self, user_message: str, conversation_id: str, city: str, user_details: Dict = None) -> Dict:
        """
        Main method to process user message and handle the complete flow
        """
        # Analyze the user request
        analysis = self.analyze_user_request(user_message, conversation_id, city)
        
        response = {
            'ai_response': analysis.get('response_text', ''),
            'needs_more_info': analysis.get('needs_more_info', True),
            'service_category': analysis.get('service_category'),
            'urgency': analysis.get('urgency', 'medium'),
            'follow_up_questions': analysis.get('follow_up_questions', []),
            'providers_contacted': None,
            'message_sent': False
        }
        
        # If ready to contact OR we have service and user details (fallback path)
        if (analysis.get('ready_to_contact') or analysis.get('service_category')) and analysis.get('service_category') and user_details:
            providers = self.get_matching_providers(analysis['service_category'], city)
            
            if providers:
                # Create message for providers
                provider_message = self.create_provider_message(user_details, analysis)
                
                # Send to top 3 providers
                send_results = self.send_to_providers(providers[:3], provider_message, user_details, analysis)
                
                response['providers_contacted'] = send_results['sent_count']
                response['message_sent'] = send_results['sent_count'] > 0
                
                # Update AI response to confirm action taken
                if send_results['sent_count'] > 0:
                    response['ai_response'] += f"\n\n✅ Perfect! I've sent your request to {send_results['sent_count']} qualified {analysis['service_category']} providers in {city}. They should contact you directly within the next few hours."
                    
                    if analysis.get('urgency') == 'high':
                        response['ai_response'] += " Since this is urgent, they've been notified to respond quickly."
                    
                    response['ai_response'] += "\n\nIs there anything else I can help you with?"
        
        return response
    
    def _handle_fallback_mode(self, user_message: str, city: str, user_details: Dict = None) -> Dict:
        """
        Fallback mode when AI API is not configured - uses local logic
        """
        # Use simple local extraction
        extracted = self._simple_extract(user_message)
        service = extracted.get('service_category')
        urgency = extracted.get('urgency', 'medium')
        
        response = {
            'response': '',
            'needs_contact_info': False,
            'service_category': service,
            'urgency': urgency,
            'providers_contacted': 0,
            'follow_up_questions': []
        }
        
        # If we identified a service
        if service:
            if not user_details or not user_details.get('name') or not user_details.get('phone'):
                response['response'] = f"Great! I can help you find a {service.lower()} in {city}. To connect you with top providers, I'll need your contact information so they can reach you with quotes."
                response['needs_contact_info'] = True
                response['follow_up_questions'] = ["What's your name?", "What's your phone number?"]
            else:
                # Try to find and contact providers
                providers = self.get_matching_providers(service, city, 3)
                if providers:
                    # Create message for providers
                    provider_message = self.create_provider_message(user_details, {
                        'service_category': service,
                        'urgency': urgency,
                        'details_collected': {'problem_description': user_message}
                    })
                    
                    # Send to providers
                    send_results = self.send_to_providers(providers, provider_message, user_details, {
                        'service_category': service,
                        'urgency': urgency
                    })
                    
                    response['providers_contacted'] = send_results['sent_count']
                    
                    if send_results['sent_count'] > 0:
                        response['response'] = f"Perfect! I've contacted {send_results['sent_count']} qualified {service.lower()} providers in {city}. They should reach out to you within the next few hours with quotes.\n\nIs there anything else I can help you with?"
                    else:
                        response['response'] = f"I found your service category ({service}) but had trouble contacting providers. Please try calling them directly or check back later."
                else:
                    response['response'] = f"I understand you need a {service.lower()} in {city}. Unfortunately, I don't have any providers for that service in our database right now. You might want to try searching online or asking for local recommendations."
        else:
            # Couldn't identify service
            response['response'] = "Hi! I'm here to help you find local service providers. Could you tell me what type of service you need? For example: electrician, plumber, cleaner, handyman, etc."
            response['follow_up_questions'] = ["What type of service do you need?", "Is this urgent?"]
        
        return response

# Create global instance
ai_agent = AIAgentService()