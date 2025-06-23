#!/bin/bash
# Test script to verify PropertySearch API functionality

set -e

API_URL="http://localhost:8000"

echo "🧪 Testing PropertySearch API..."

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
if curl -f -s "$API_URL/health" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: Root endpoint
echo "2️⃣ Testing root endpoint..."
if curl -f -s "$API_URL/" | grep -q "PropertySearch API"; then
    echo "✅ Root endpoint working"
else
    echo "❌ Root endpoint failed"
    exit 1
fi

# Test 3: Examples endpoint
echo "3️⃣ Testing examples endpoint..."
if curl -f -s "$API_URL/search/examples" | grep -q "austin_rentals"; then
    echo "✅ Examples endpoint working"
else
    echo "❌ Examples endpoint failed"
    exit 1
fi

# Test 4: Search endpoint with minimal parameters
echo "4️⃣ Testing search endpoint (minimal)..."
SEARCH_RESPONSE=$(curl -f -s -X POST "$API_URL/search" \
    -H "Content-Type: application/json" \
    -d '{
        "listing_type": "both",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "radius_miles": 5.0
    }')

if echo "$SEARCH_RESPONSE" | grep -q '"success":true'; then
    echo "✅ Basic search endpoint working"
    echo "📊 Response preview:"
    echo "$SEARCH_RESPONSE" | jq '.message, .count' 2>/dev/null || echo "$SEARCH_RESPONSE" | head -c 200
else
    echo "❌ Search endpoint failed"
    echo "🐛 Response: $SEARCH_RESPONSE"
    exit 1
fi

# Test 5: Search endpoint with detailed parameters
echo "5️⃣ Testing search endpoint (detailed)..."
DETAILED_SEARCH=$(curl -f -s -X POST "$API_URL/search" \
    -H "Content-Type: application/json" \
    -d '{
        "listing_type": "rental",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "radius_miles": 10.0,
        "min_rent_price": 1000,
        "max_rent_price": 3000,
        "min_beds": 1,
        "home_types": ["CONDO", "SINGLE_FAMILY"]
    }')

if echo "$DETAILED_SEARCH" | grep -q '"success":true'; then
    echo "✅ Detailed search endpoint working"
    LISTING_COUNT=$(echo "$DETAILED_SEARCH" | jq '.count' 2>/dev/null || echo "unknown")
    echo "📈 Found $LISTING_COUNT listings"
else
    echo "❌ Detailed search failed"
    echo "🐛 Response: $DETAILED_SEARCH"
    exit 1
fi

echo ""
echo "🎉 All API tests passed!"
echo "🔗 API Documentation: $API_URL/docs"
echo "📊 Monitor logs: docker logs -f property-agent" 