# Project Brief: ConnectYou Canada Day

## Overview
ConnectYou Canada Day is a web-based service provider directory that connects customers with local service providers across Canadian cities. The platform serves as a bridge between people needing services and skilled professionals who can provide them.

## Core Purpose
- **For Customers**: Find, contact, and hire trusted local service providers quickly and easily
- **For Service Providers**: Get connected with potential customers in their area
- **For Administrators**: Manage the platform, providers, and ensure quality service

## Key Features
- City-based service provider directory
- Multiple service categories (electrician, plumber, HVAC, handyman, etc.)
- Direct calling and texting capabilities via Twilio integration
- Provider rating and review system
- Report system for provider feedback
- Admin dashboard for platform management
- Provider registration and management
- Mobile-responsive design with dark/light themes

## Target Users
1. **Customers**: Homeowners, renters, and businesses needing professional services
2. **Service Providers**: Licensed and skilled professionals seeking customers
3. **Administrators**: Platform managers overseeing quality and operations

## Technical Foundation
- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Database**: SQLite with Flask-Migrate for schema management
- **Frontend**: HTML/CSS/JavaScript with Bootstrap for responsive design
- **Communications**: Twilio for SMS/calling, email services for notifications
- **Architecture**: Monolithic web application with RESTful API endpoints

## Success Metrics
- Number of active service providers per city
- Customer engagement (calls, texts, reports)
- Provider satisfaction and retention
- Platform usage analytics
- Quality of service connections

## Current Status
The application is functional with provider-customer matching capabilities, communication features, and administrative tools. Recent work focused on fixing frontend-backend integration for provider display functionality. 