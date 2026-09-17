# Feeder Van Board

A mobile-friendly, lightweight web application built for rural commuters to log and track shared informal van schedules.

## Links
- **Prototype Link:** https://feeder-van-board.onrender.com

## Design Decisions: Duplicate Handling & Data Trust

Designing for a low-technical-literacy, rural environment requires balancing data integrity against friction. Traditional authentication (passwords, SMS OTPs) would immediately alienate the primary user base. 

To build **Data Trust** without heavy auth walls, the app relies on frictionless device fingerprinting (a persistent, secure `deviceId` cookie). This allows the system to confidently associate actions with specific users without requiring a login. 

Because we rely on this anonymous device ID, there is a risk of bad actors wiping their cookies to manipulate the system. We accepted this trade-off because the barrier to entry must remain near-zero; the community-driven "upvote" (confirmation) system naturally bubbles legitimate vans to the top, mitigating spam. A user can securely delete only the trips they originated, and cannot upvote their own vans, enforcing basic integrity.

**Duplicate Handling** is managed proactively rather than correctively. Instead of allowing messy duplicate entries and trying to merge them later, the server intercepts submissions that match an existing active trip (same route, same landmark, similar timeframe) and immediately prompts the user with a "Duplicate Detected" modal. This intercepts the creation of a duplicate row and instead converts the user's intent into a "confirmation" (upvote) on the existing trip. The trade-off here is slight friction for the second user submitting an identical van, but it results in a much cleaner, more trustworthy public board for all commuters relying on the schedule.
