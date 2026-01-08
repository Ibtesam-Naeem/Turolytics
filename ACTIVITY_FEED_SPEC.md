# Activity Feed Specification

## Overview
The Activity Feed is a unified chronological feed showing all business activity from Turo and banking sources.

## Data Sources

### 1. Recent Turo Transactions
**Source:** Scraped Turo transaction history page

**Includes:**
- Turo payouts (when money is received from Turo)
- Refunds and adjustments
- Any other Turo-related financial transactions

**Display Format:**
```
Turo Transaction: [Type] - [Amount] on [Date] (Reservation #[ID])
```

**Example:**
- "Turo Transaction: Payment - CA$1,820.40 on Aug 30, 2025 (Reservation #48583244)"
- "Turo Transaction: Refund - -CA$4.94 on Aug 30, 2025 (Reservation #48583244)"

### 2. Recent Banking Transactions
**Source:** Connected bank accounts via Plaid/banking integration

**Includes:**
- Purchases (fuel, maintenance, etc.)
- Payments (loan payments, insurance, etc.)
- Deposits (Turo payouts that hit the bank)
- Any other banking activity

**Display Format:**
```
Banking Transaction: [Merchant/Description] - [Amount] on [Date]
```

**Example:**
- "Banking Transaction: Turo Payout - $2,845.00 on Nov 28"
- "Banking Transaction: Shell Gas Station - -$65.00 on Nov 27"
- "Banking Transaction: AutoZone - -$120.00 on Nov 27"

### 3. New Bookings
**Source:** Turo trips data (`turo_trips` table where `trip_type = 'booked_trips'`)

**Display Format:**
```
New Booking: [Guest Name]'s trip with [Vehicle Name] - [X] days - [Total Amount] starting [Date]
```

**Required Information:**
- Car/Vehicle name
- Number of days (calculated from start_date to end_date)
- Total amount (trip earnings)

**Example:**
- "New Booking: John's trip with Hyundai Elantra 2017 - 5 days - CA$450.00 starting Dec 15, 2025"

### 4. Cancellations
**Source:** Turo trips data (trips with status = 'CANCELLED' or 'CANCELED')

**Display Format:**
```
Cancellation: [Guest Name]'s trip with [Vehicle Name] cancelled on [Date]
```

**Example:**
- "Cancellation: Jane's trip with Genesis G70 2022 cancelled on Dec 10, 2025"

## Display Rules

1. **Chronological Order:** All activities sorted by date/time (most recent first)
2. **Unified Feed:** All activity types mixed together in one chronological list
3. **Real-time Updates:** Feed updates when new data is scraped or received
4. **Date Formatting:** Use consistent date format (e.g., "Dec 15, 2025" or "Nov 28")

## What's NOT Included

The Activity Feed does NOT include:
- ❌ Fleet health alerts (these go in Fleet Health Card)
- ❌ Maintenance reminders (these go in Maintenance Timeline Card)
- ❌ Vehicle status changes (unless related to a booking/cancellation)
- ❌ General vehicle updates

## Implementation Notes

- Turo transactions will be scraped from the transaction history page
- Banking transactions require Plaid/banking integration
- New bookings are detected when new trips are scraped with `trip_type = 'booked_trips'`
- Cancellations are detected when trip status changes to 'CANCELLED'/'CANCELED'
- All activities should have timestamps for proper chronological sorting

