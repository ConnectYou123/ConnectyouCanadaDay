class ChatWidget {
  constructor() {
    this.isOpen = false;
    this.isSubmitting = false;
    this.chatPollInterval = null;
    this.currentPollingPhone = null;
    this.isTyping = false;
    this.lastMessageCount = 0;
    this.unmatchedMessageCount = 0;
    this.maxUnmatchedMessages = 3;

    // Bot identity customization with defaults
    this.botName = 'Suzy Q';
    this.botAvatarUrl = '/static/images/user.svg';
    this.description = '';

    // Start fetching bot icon info, then initialize widget and polling
    this.fetchAndUpdateBotIcon()
      .finally(() => {
        this.init();

        // Poll bot icon info every 30 seconds for updates
        this.botIconPollInterval = setInterval(() => {
          this.fetchAndUpdateBotIcon();
        }, 5000);
      });

    this.conversationState = {
      stage: 'initial',
      category: null,
      location: null,
      budget: null,
      preferences: []
    };

    this.serviceCategories = {
      'Electrician': [
        { description: '🔧 Repairs/installations of wiring, lighting, panels, and outlets are essential, frequent, and safety-critical.' }
      ],
      'Plumber': [
        { description: '🚰 Urgently needed for leaks, clogs, water heater issues, and general pipe maintenance.' }
      ],
      'HVAC Technician': [
        { description: '❄️🔥 Handles heating and cooling systems—especially crucial in extreme weather seasons.' }
      ],
      'General Handyman': [
        { description: '🛠️ Ideal for smaller, ongoing household fixes like mounting, patching, and basic repairs.' }
      ],
      'House Cleaner': [
        { description: '🧼 Routine or deep cleaning is consistently in demand for upkeep, moving, or post-reno situations.' }
      ],
      'Painter': [
        { description: '🎨 Interior and exterior painting is often part of maintenance, renovation, or preparing a home for sale.' }
      ],
      'Pest Control': [
        { description: '🐜 Needed seasonally and urgently for infestations—prevention and removal are both critical.' }
      ],
      'Roofing Specialist': [
        { description: '🏠 Vital for leak repairs, storm damage, and routine inspections—especially in climates with harsh winters or storms.' }
      ],
      'Appliance Repair Technician': [
        { description: '🔌 Homeowners often need quick fixes for essential appliances like fridges, washers, and dryers.' }
      ]
    };
  }

  // Fetch bot icon/name/description from API, update if changed
  async fetchAndUpdateBotIcon() {
    try {
      const res = await fetch('/api/chat-icons');
      if (!res.ok) throw new Error(`Status: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        const firstIcon = data[0];
        const newName = firstIcon.name || 'Suzy Q';
        const newAvatar = firstIcon.image_url || '/static/images/user.svg';
        const newDescription = firstIcon.description || '';

        let changed = false;
        if (newName !== this.botName) {
          this.botName = newName;
          changed = true;
        }
        if (newAvatar !== this.botAvatarUrl) {
          this.botAvatarUrl = newAvatar;
          changed = true;
        }
        if (newDescription !== this.description) {
          this.description = newDescription;
          changed = true;
        }

        if (changed) {
          this.updateBotHeaderUI();
          this.updateMessagesBotAvatar();
          this.updateWelcomeMessageText();
        }
      }
    } catch (err) {
      console.error('Failed to update bot icon:', err);
    }
  }

  // Update header: avatar image, name text, description text
  updateBotHeaderUI() {
    const header = document.querySelector('.chat-header');
    if (!header) return;

    const avatarImg = header.querySelector('.bot-avatar-header img.avatar-img');
    if (avatarImg) {
      avatarImg.src = this.botAvatarUrl;
      avatarImg.alt = this.botName;
    }

    const h1 = header.querySelector('h1');
    if (h1) h1.textContent = this.botName;

    const p = header.querySelector('p');
    if (p) p.textContent = this.description;
  }

  // Update avatar images in all existing bot messages in chat window
  updateMessagesBotAvatar() {
    const botAvatars = document.querySelectorAll('.chat-messages .bot-avatar img.avatar-img');
    botAvatars.forEach(img => {
      img.src = this.botAvatarUrl;
      img.alt = this.botName;
    });
  }

  // Update the "I'm [botName], here to help..." welcome message text live
  updateWelcomeMessageText() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    // Find the paragraph with class 'welcome-text' inside bot message
    const welcomeParagraph = chatMessages.querySelector('.message.bot p.welcome-text');
    if (welcomeParagraph) {
      welcomeParagraph.innerHTML = `I'm ${this.botName}, here to help you find the perfect service provider for your needs. What type of service are you looking for?`;
    }
  }

  formatPhoneNumber(phone) {
    if (!phone) return '';
    phone = phone.trim();
    if (phone.startsWith('+')) {
      phone = '+' + phone.slice(1).replace(/\D/g, '');
    } else {
      phone = '+' + phone.replace(/\D/g, '');
    }
    return phone;
  }

  init() {
    this.createWidget();
    this.attachEventListeners();
    this.updateUserInfoVisibility();
    this.injectCityStyles();

    const phone = sessionStorage.getItem('chatPhone');
    if (phone) {
      this.currentPollingPhone = phone;
      this.loadChatMessages(phone);
    } else {
      this.addWelcomeMessage();
    }
  }

  createWidget() {
    const widgetHTML = `
      <div class="chat-widget">
        <button class="chat-toggle" id="chatToggle"><i class="fas fa-comments"></i></button>
        <div class="chatbot-container" id="chatBox" style="display:none;">
          <div class="chat-header">
            <div class="bot-avatar-header">
              <img src="${this.botAvatarUrl}" alt="${this.botName}" class="avatar-img"/>
            </div>
            <h1>${this.botName}</h1>
            <p style="margin-bottom: 0;">${this.description}</p>
          </div>
          <div class="chat-messages" id="chatMessages"></div>
          <div class="chat-user-info" id="chatUserInfo">
            <input type="text" class="input-field" id="chatUsername" placeholder="Your Name" />
            <input type="email" class="input-field" id="chatEmail" placeholder="Your Email" />
            <input type="tel" class="input-field" id="chatPhone" placeholder="+9779809778080" />
          </div>
          <div class="chat-input">
            <input type="text" class="input-field" id="chatInput" placeholder="Type your message..." />
            <button class="send-button" id="chatSendBtn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13"></path><path d="M22 2L15 22L11 13"></path><path d="M22 2L2 9L11 13"></path>
              </svg>
            </button>
          </div>
          <div id="chatStatus" class="chat-status"></div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    this.injectAvatarStyles();
  }

  injectAvatarStyles() {
    const style = document.createElement('style');
    style.innerHTML = `
      .avatar-img {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
      }
      .bot-avatar-header {
        display: inline-block;
        vertical-align: middle;
        margin-right: 8px;
      }
      .chat-header h1 {
        display: inline-block;
        vertical-align: middle;
        margin: 0 0 0 8px;
        font-size: 1.2em;
      }
      .bot-avatar {
        display: inline-block;
        vertical-align: top;
        margin-right: 8px;
      }
    `;
    document.head.appendChild(style);
  }

  injectCityStyles() {
    const style = document.createElement('style');
    style.innerHTML = `
      .city-choices {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
      }
      .city-item1 {
        cursor: pointer;
        background-color: #007BFF;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        user-select: none;
        transition: background-color 0.3s ease;
        display: inline-block;
      }
      .city-item1:hover {
        background-color: #0056b3;
      }
      .city-toronto {
        background-color: #e63946;
      }
      .city-toronto:hover {
        background-color: #a6282a;
      }
      .city-barrie {
        background-color: #2a9d8f;
      }
      .city-barrie:hover {
        background-color: #1f6f66;
      }
      .other-services-static {
        background-color: #6c757d !important;
        color: #fff !important;
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        user-select: none;
        display: inline-block;
        transition: background-color 0.3s ease;
      }
      .other-services-static:hover {
        background-color: #495057 !important;
      }
    `;
    document.head.appendChild(style);
  }

  attachEventListeners() {
    document.getElementById('chatToggle').addEventListener('click', (e) => {
      e.preventDefault();
      this.toggleChat();
    });

    document.getElementById('chatSendBtn').addEventListener('click', () => this.sendMessage());

    document.getElementById('chatInput').addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  updateUserInfoVisibility() {
    const usernameInput = document.getElementById('chatUsername');
    const emailInput = document.getElementById('chatEmail');
    const phoneInput = document.getElementById('chatPhone');
    const userInfoDiv = document.getElementById('chatUserInfo');

    usernameInput.value = sessionStorage.getItem('chatName') || '';
    emailInput.value = sessionStorage.getItem('chatEmail') || '';
    phoneInput.value = sessionStorage.getItem('chatPhone') || '';

    userInfoDiv.style.display = (usernameInput.value || emailInput.value || phoneInput.value) ? 'none' : 'block';
  }

  toggleChat() {
    this.isOpen ? this.closeChat() : this.openChat();
  }

  openChat() {
    const chatBox = document.getElementById('chatBox');
    document.getElementById('chatToggle').innerHTML = '<i class="fas fa-times"></i>';
    this.isOpen = true;
    if (chatBox) {
      chatBox.style.display = 'flex';
      chatBox.classList.add('active');
    }
    setTimeout(() => document.getElementById('chatInput')?.focus(), 250);

    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages.innerHTML.trim()) {
      this.addWelcomeMessage();
    }
  }

  closeChat() {
    const chatBox = document.getElementById('chatBox');
    document.getElementById('chatToggle').innerHTML = '<i class="fas fa-comments"></i>';
    this.isOpen = false;
    if (chatBox) {
      chatBox.style.display = 'none';
      chatBox.classList.remove('active');
    }
    this.stopChatPolling();
  }

  addWelcomeMessage() {
    const chatMessages = document.getElementById('chatMessages');
    const welcomeHTML = `
      <div class="message bot">
        <div class="bot-avatar">
          <img src="${this.botAvatarUrl}" alt="${this.botName}" class="avatar-img"/>
        </div>
        <div class="message-content">
          <p>Welcome to ConnectYou.pro! 👋</p>
          <p class="welcome-text">I'm ${this.botName}, here to help you find the perfect service provider for your needs. What type of service are you looking for?</p>
          <div class="quick-replies">
            ${Object.keys(this.serviceCategories).map(cat => `<div class="quick-reply">${cat}</div>`).join('')}
          </div>
        </div>
      </div>
    `;
    chatMessages.innerHTML = welcomeHTML;
    this.attachQuickReplyListeners();
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  }

  attachQuickReplyListeners() {
    const replies = document.querySelectorAll('.quick-reply');
    replies.forEach(reply => {
      reply.addEventListener('click', () => {
        if (reply.classList.contains('other-services-static')) {
          this.resetConversation();
          return;
        }
        const category = reply.textContent.trim();
        this.unmatchedMessageCount = 0;
        this.addMessage(category, true);
        this.processMessage(category);
      });
    });
  }

  attachCitySelectionListeners() {
    const cityItems = document.querySelectorAll('.city-item1');
    cityItems.forEach(cityItem => {
      cityItem.addEventListener('click', () => {
        const cityName = cityItem.getAttribute('data-city-name');
        window.selectedCity = cityName;
        const serviceType = this.conversationState.category;
        if (typeof window.viewProviders === 'function' && serviceType) {
          window.viewProviders(serviceType);
        } else {
          console.warn('viewProviders function not found or serviceType missing');
        }
      });
    });
  }

  async fetchCities() {
    try {
      const response = await fetch('/api/get-active-cities');
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      if (data.success && Array.isArray(data.cities)) {
        return data.cities;
      }
      return [];
    } catch (error) {
      console.error('Failed to fetch cities:', error);
      return [];
    }
  }

  async handleCategorySelection(category) {
    const services = this.serviceCategories[category];
    let response = `Great! Here's what we offer in <strong>${category.toLowerCase()}</strong>:<br><br>`;

    services.forEach(service => {
      response += `
        <div class="service-card">
          <div class="service-description">${service.description}</div>
        </div>`;
    });

    const cities = await this.fetchCities();

    if (cities.length > 0) {
      response += `<br><p><strong>Select your preferred city:</strong></p><div class="city-choices">`;
      cities.forEach(city => {
        response += `
          <div class="city-item1" data-city-name="${city.name}" data-city-emoji="${city.emoji || ''}">${city.emoji || ''} ${city.name}</div>
        `;
      });
      response += `</div>`;
    } else {
      response += `<br><p>No available cities at the moment.</p>`;
    }

    response += `
      <br>
      <div class="quick-replies">
        <div class="quick-reply other-services-static">Other Services</div>
      </div>
    `;

    return response;
  }

  addMessage(content, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    messageDiv.innerHTML = isUser
      ? `<div class="message-content">${content}</div>`
      : `<div class="bot-avatar"><img src="${this.botAvatarUrl}" alt="${this.botName}" class="avatar-img"/></div><div class="message-content">${content}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    return messageDiv;
  }

  showTemporaryNotification(text, duration = 5000) {
    const chatMessages = document.getElementById('chatMessages');
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'message bot notification';
    notificationDiv.innerHTML = `
      <div class="bot-avatar"><img src="${this.botAvatarUrl}" alt="${this.botName}" class="avatar-img"></div>
      <div class="message-content">${text}</div>
    `;
    chatMessages.appendChild(notificationDiv);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    setTimeout(() => {
      notificationDiv.remove();
    }, duration);
  }

  processMessage(message) {
    this.isTyping = true;
    const typing = this.showTyping();

    setTimeout(() => {
      typing.remove();
      this.isTyping = false;

      const lowerMessage = message.toLowerCase();
      const matchedCategory = Object.keys(this.serviceCategories).find(cat => cat.toLowerCase() === lowerMessage);

      if (matchedCategory) {
        this.unmatchedMessageCount = 0;
        this.conversationState.category = matchedCategory;
        this.conversationState.stage = 'category_selected';

        this.handleCategorySelection(matchedCategory).then(response => {
          this.addMessage(response);
          this.attachQuickReplyListeners();
          this.attachCitySelectionListeners();
        });

        return;
      }

      let response = '';
      switch (this.conversationState.stage) {
        case 'initial':
          this.unmatchedMessageCount++;
          response = this.handleGeneralQuery(message);
          break;
        case 'category_selected':
          if (lowerMessage.includes('location') || lowerMessage.includes('area') || lowerMessage.includes('city')) {
            this.conversationState.stage = 'location_gathering';
            response = `Great! What's your location or preferred service area?`;
          } else if (lowerMessage.includes('budget') || lowerMessage.includes('price') || lowerMessage.includes('cost')) {
            this.conversationState.stage = 'budget_gathering';
            response = `What's your budget range for this service? (e.g., $50-100, $500-1000, etc.)`;
          } else {
            this.unmatchedMessageCount++;
            response = this.handleServiceInquiry(message);
          }
          break;
        case 'location_gathering':
          this.conversationState.location = message;
          this.conversationState.stage = 'details_gathering';
          this.unmatchedMessageCount = 0;
          response = `Got it! Your location is ${message}. Any specific preferences for your ${this.conversationState.category.toLowerCase()} service?`;
          break;
        case 'budget_gathering':
          this.conversationState.budget = message;
          this.conversationState.stage = 'details_gathering';
          this.unmatchedMessageCount = 0;
          response = `Thanks! Budget set to ${message}. Any preferences for your ${this.conversationState.category.toLowerCase()} service?`;
          break;
        case 'details_gathering':
          this.conversationState.preferences.push(message);
          this.unmatchedMessageCount = 0;
          response = this.generateRecommendations();
          break;
        default:
          this.unmatchedMessageCount++;
          response = this.handleGeneralQuery(message);
      }

      if (this.unmatchedMessageCount >= this.maxUnmatchedMessages) {
        this.resetConversation();
        return;
      }

      this.addMessage(response);
    }, 1000 + Math.random() * 1000);
  }

  resetConversation() {
    this.stopChatPolling();
    this.isTyping = false;
    this.unmatchedMessageCount = 0;
    this.lastMessageCount = 0;

    this.conversationState = {
      stage: 'initial',
      category: null,
      location: null,
      budget: null,
      preferences: []
    };

    this.addWelcomeMessage();

    const userInfoDiv = document.getElementById('chatUserInfo');
    userInfoDiv.style.display = 'block';

    document.getElementById('chatUsername').value = '';
    document.getElementById('chatEmail').value = '';
    document.getElementById('chatPhone').value = '';

    sessionStorage.clear();
  }

  showStatusNotification(text, duration = 5000) {
    const statusDiv = document.getElementById('chatStatus');
    if (!statusDiv) return;
    statusDiv.textContent = text;
    statusDiv.style.opacity = '1';
    setTimeout(() => {
      statusDiv.style.opacity = '0';
      setTimeout(() => {
        statusDiv.textContent = '';
      }, 500);
    }, duration);
  }

  handleServiceInquiry() {
    const responses = [
      `To help you better, could you share your location?`,
      `What's your preferred service area?`,
      `Can you tell me your budget range?`,
      `Do you have any specific preferences for the service?`
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  }

  handleGeneralQuery(message) {
    const lower = message.toLowerCase();
    if (lower.includes('help') || lower.includes('how') || lower.includes('what')) {
      return `I'm here to help you find the perfect provider! 😊<br><br>Tell me what kind of service you need, your location, and budget.`;
    } else if (lower.includes('price') || lower.includes('budget')) {
      return `Prices vary by service. What's your budget and what service do you need?`;
    } else if (lower.includes('location') || lower.includes('near')) {
      return `We match you with nearby providers. What's your location?`;
    } else {
      return `Tell me:<br>• What service you need<br>• Your location<br>• Your budget<br><br>Or select a category above 👆`;
    }
  }

  generateRecommendations() {
    const { category = 'services', location = 'your area', budget = 'your budget' } = this.conversationState;
    return `Searching for <strong>${category.toLowerCase()}</strong> providers in <strong>${location}</strong> within <strong>${budget}</strong>.<br><br>
      🔍 Matching top-rated professionals for you...<br><br>
      Would you like me to show them now or adjust any details?`;
  }

  sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    const name = document.getElementById('chatUsername').value.trim();
    const email = document.getElementById('chatEmail').value.trim();
    const phoneRaw = document.getElementById('chatPhone').value.trim();
    const phone = this.formatPhoneNumber(phoneRaw);

    // Store user info in sessionStorage
    sessionStorage.setItem('chatName', name);
    sessionStorage.setItem('chatEmail', email);
    sessionStorage.setItem('chatPhone', phone);

    this.updateUserInfoVisibility(); // Hide inputs if user info is provided
    input.value = '';

    this.addMessage(message, true);

    this.showStatusNotification('We have notified the admin. We will contact you soon.');
    this.sendChatMessageToServer({ name, email, phone, message });
  }

  async sendChatMessageToServer({ name, email, phone, message }) {
    try {
      const response = await fetch('/api/send-chat-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, message })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();

      if (data.success) {
        this.currentPollingPhone = phone;
        this.loadChatMessages(phone);
      } else {
        this.addMessage('Failed to send message. Please try again.', false);
      }
    } catch (err) {
      console.error('Error sending chat message:', err);
      this.addMessage('Error sending message. Please check your connection.', false);
    }
  }

  showTyping() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.innerHTML = `
      <div class="bot-avatar"><img src="${this.botAvatarUrl}" alt="${this.botName}" class="avatar-img"/></div>
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
      </div>`;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    return typingDiv;
  }

  stopChatPolling() {
    if (this.chatPollInterval) {
      clearInterval(this.chatPollInterval);
      this.chatPollInterval = null;
    }
    this.lastMessageCount = 0;
  }

  async loadChatMessages(phone) {
    try {
      const response = await fetch('/api/get-chat-messages-by-phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      const chatMessages = document.getElementById('chatMessages');
      if (data.success && data.messages.length > 0) {
        if (data.messages.length !== this.lastMessageCount) {
          this.lastMessageCount = data.messages.length;
          chatMessages.innerHTML = '';
          data.messages.forEach(msg => {
            this.addMessage(msg.text, msg.sender === 'user');
          });
        }
      } else {
        this.addWelcomeMessage();
        this.lastMessageCount = 0;
      }

      if (!this.chatPollInterval) {
        this.chatPollInterval = setInterval(() => {
          this.loadChatMessages(phone);
        }, 5000);
      }
    } catch (err) {
      console.error('Failed to load chat messages:', err);
      this.resetConversation();
    }
  }
}

let chatWidgetInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  chatWidgetInstance = new ChatWidget();
});
