# Local SEO Analysis: unit11.co

Audit date: 2026-10-15

Evidence base: homepage, contact page, robots.txt, both sitemaps, all 95 location and Kent hub pages, 4 service pages, the blog index and post list, response headers. Not available: Google Business Profile data, live local pack rankings, backlink data, DataForSEO. Where a check could not be completed, it is marked as unverified rather than guessed.

## Local SEO Score: 42/100

| Dimension | Weight | Score | Headline |
|---|---|---|---|
| GBP signals | 25% | 14/25 | CID link exists only in schema. No embed, hours or category cues on page |
| Reviews and reputation | 20% | 3/20 | No review count, rating or testimonials. Ceramic pages show another service's review blurb |
| Local on-page | 20% | 7/20 | Strong service pages, but 90 near-duplicate town pages and no local proof |
| NAP and citations | 15% | 8/15 | Phone and address fields disagree across page and schema. Citations unverified |
| Local schema | 10% | 6/10 | Present everywhere, but duplicated, partly invalid, same on every town page |
| Local links and authority | 10% | 4/10 | Few visible signals. Backlinks not measurable here |
| **Total** | 100% | **42/100** | |

An earlier quick pass scored this 52. That figure included a manual uplift. This version is a straight weighted sum, and the full crawl turned up more problems than the sample did.

## Business type

Hybrid, leaning brick-and-mortar. Real unit address (Unit 11, Railway Street Industrial Estate, Railway Street, Gillingham, Kent, ME7 1YQ) with a 20 km service radius declared in schema, plus 90 town pages that reach well beyond that radius.

## Industry vertical

Automotive services, but not a dealership: detailing, ceramic coating, XPEL PPF, restoration, mechanical servicing, ECU remapping, exhausts. The skill's automotive path targets dealerships, so I used the generic `LocalBusiness` path with `AutoRepair` as the better subtype. The schema currently uses plain `LocalBusiness`.

---

## 1. GBP signals (14/25)

| Signal | Status |
|---|---|
| Place link in schema (`hasMap`, CID 13808659323212161400) | Present in one schema block. A second block uses a coordinates search URL instead |
| Embedded Google Map on any page | **None found on 95 location pages, homepage or contact page** |
| Opening hours visible in page text | Not found. Only in schema, as free text |
| `tel:` click-to-call | Present on homepage (07360 280307) |
| Reviews widget | None |
| Social profiles | Facebook, Instagram, YouTube, TikTok in footer |
| FAQ-style content to replace deprecated GBP Q&A | Present on 1 of 95 location pages and on `/ppf-installer/`. Missing elsewhere |
| GBP primary category | Unverified (needs GBP access) |

Notes:
- A web search for the business name, address and postcode returned no GBP, directory or review listings. That is not proof they do not exist, but it means the business is not easy to find from the open web with those queries.
- Do not point the GBP website link at a page that competes with a stronger organic page (Sterling Sky Diversity Update). The homepage is usually correct for a single-location business, so keep that unless a service page is the stronger target.
- Recommended GBP setup for this business: primary category matching the highest-revenue service (for example "Car detailing service"), secondary categories for paint protection, car restoration, auto repair and ECU tuning where Google offers them, and service areas limited to places you actually serve.

## 2. Reviews and reputation (3/20)

- No review count, star rating, testimonial block or third-party badge on the homepage.
- No `aggregateRating` in any schema block on any crawled page.
- All 50 ceramic coating town pages carry a "customer reviews" section, but the copy introducing it refers to customers who "have already had their remap". That is ECU remapping text pasted into ceramic coating pages. It misleads visitors and weakens topical relevance.
- Review velocity (18-day rule), owner response rate, and rating cannot be measured from the site. Check in GBP.
- Healthcare and legal review rules do not apply here. General rule applies: no review gating (Google fake engagement policy, FTC penalties).

## 3. Local on-page SEO (7/20)

### Strengths
- Dedicated service pages exist for the main services (ceramic coating, PPF, restoration, servicing, ECU remapping, body repair, dent removal, caliper painting). This is the top local organic factor and the site does well here.
- Titles on hub pages carry Kent and the service (for example "Paint Protection Film Kent | XPEL PPF Installer | Unit 11").
- Clean canonicals on all 95 pages, no accidental `noindex`, working XML sitemaps, fast server response (about 0.17 s TTFB on the homepage; HTML is 321 KB).

### Location page audit (full crawl, 95 pages)

| Group | Pages | Words per page | Same text after swapping the town name |
|---|---|---|---|
| `ceramic-coating-in-{town}` | 50 | 2,146 to 2,165 | **98.8% to 99.6% identical** (14 random pairs, average 99.3%) |
| `paint-protection-film-{town}` | 40 | 1,865 to 2,487 (average 1,890) | **88.2% to 90.2% identical** (14 random pairs, average 89.4%) |
| Kent hub pages | 5 | n/a | Distinct |

Further findings:
- Word counts include menu and footer boilerplate, so real unique copy is lower still.
- The only town-specific text is the town name, mentioned an average of 7 times (ceramic) and 4 times (PPF). Some pages mention it zero times in body copy.
- Meta descriptions are technically unique (50 of 50 and 40 of 40) but are the same sentence with the town swapped. Title patterns repeat in 3 templates.
- No Google Map, local photos, local testimonials, drive time, landmarks, or named local jobs on any town page.
- Only 1 of 95 town pages has FAQ markup. Only 1 has `Service` markup.
- The 90 pages reach towns far from Gillingham, including Chelmsford, Brentwood, Romford, Westminster, Islington, Walthamstow, Edmonton, Croydon, Carshalton and Crowborough. The schema says the service area is a 20 km radius, so the site contradicts itself.
- The two sets cover different towns: 30 towns have only a ceramic page, 20 have only a PPF page, 20 have both. There is no evident logic for which service is offered where.
- Only 40 PPF town pages are linked from `/ppf-installer/` and 50 ceramic ones from `/ceramic-coating-kent/`. The homepage links to none. That keeps them reachable but gives them thin link equity, and they sit in a flat list of 40 to 50 links.
- Brand claim check: ceramic town pages say "Feynlab" coatings, while the Kent hub page title says "Gyeon and Gtechniq Certified". All three brands are named on all pages, so the pages do not tell a visitor which product they will actually get.

**Skill quality gate:** 50+ location pages is a HARD STOP condition. This audit makes no recommendation to create further pages. The only pages worth keeping are those for towns where you can show genuine local work.

Risk assessment: this matches the doorway pattern the skill cites (swap the city and the page still reads the same). The March 2024 Core Update case study in the skill saw 80% ranking and 63% traffic loss for the same pattern. The ceramic set is the higher risk because it is nearly byte-identical.

### Other on-page issues
- Homepage H1 is a rotating animated headline ("From Servicing / Tuning / Detailing / Restoring to Perfection") with no town or service keyword in static text.
- Homepage title has "Kent" but not "Gillingham".
- 10 of 11 homepage images have empty alt text.
- 45 blog posts, many overlapping: several near-duplicate topics ("shield your car's paint from environmental hazards" and "...threats", "mastering paint correction" three ways, "best car wax" twice, "boost your car's value" three ways, "interior care" four ways). This is keyword cannibalisation and likely thin, AI-written filler. Blog posts also contain only 3 location links, so they do not support the town pages.
- Transactional and utility URLs sit in the sitemap: cart, checkout, my-account, dashboard, thank-you pages, lottery pages, booking steps, and legacy `-old` pages (`classic-car-restoration-old`, `foundation-detail-old`, `correction-detail-old`, `contact-us-2`, `services-1`, `services-2`).
- Footer copyright is inconsistent (2023 to 2025 in one place, 2024 in another) and two legal names appear (Unit Eleven Ltd, Unit 11).

## 4. NAP consistency and citations (8/15)

| Source | Name | Address | Phone |
|---|---|---|---|
| Footer and contact | Unit-11 / Unit Eleven Ltd | Unit 11 Railway Street Industrial Estate, Railway Street, Gillingham, Kent, ME7 1YQ | 07360 280307 |
| Schema block 1 (Rank Math graph) | UNIT-11 | Street "11, Railway Street Industrial Estate"; locality **"Railway St"**; region **"Gillingham"** | +44 3333 058378 |
| Schema block 2 (custom LocalBusiness) | UNIT-11 | Street "11, Railway Street Industrial Estate, Railway St"; locality Gillingham; region Kent | +44 3333 058378 |

Discrepancies:
1. **Critical:** the number users can call (07360 280307) differs from the number in schema (+44 3333 058378).
2. **Critical:** schema block 1 has locality and region swapped.
3. Two entity IDs for the same business (`https://unit11.co/#organization` and `https://unit11.co`), with different emails (bookings@ and hello@).
4. Name variants: UNIT-11, Unit-11, Unit 11, Unit Eleven Ltd.
5. Facebook `sameAs` value `https://facebook.com/@weareunit11` is malformed and conflicts with `https://www.facebook.com/weareunit11/` in block 2.

### Citation presence (web searches, not conclusive)
| Directory | Result |
|---|---|
| Yelp, Yell, Checkatrade, Trustpilot | No listing found for "unit11" or "Unit Eleven" Gillingham |
| XPEL installer directory | No listing found for the Gillingham address |
| Bing Places, Apple Business Connect | Cannot be verified from outside the account. Check directly |
| BBB (low value in the UK) | Not checked |

Because the search tool is US-focused, treat these as "not found" rather than "does not exist". UK directories worth checking and claiming: Google Business Profile, Bing Places, Apple Business Connect, Yell, Thomson Local, Checkatrade or TrustATrader if relevant, FreeIndex, Facebook, and the manufacturer installer locators for XPEL, Gyeon, Gtechniq and Feynlab. Submit to the data aggregators (Data Axle, Foursquare, and UK equivalents) for downstream distribution.

## 5. Local schema (6/10)

Present on every page, but:

| Issue | Where |
|---|---|
| Two overlapping entities (Rank Math graph plus hand-written block) | All pages |
| Plain `LocalBusiness` rather than `AutoRepair` or similar subtype | All pages |
| `openingHours` is a sentence, not `openingHoursSpecification` | Block 2 |
| `additionalProperty` is a URL string | Block 2 |
| `currenciesAccepted: "$"` for a GBP business | Block 2 |
| `priceRange: "100-10000"` | Block 2 |
| `ContactPoint` used as a property name (should be `contactPoint`) | Block 2 |
| Empty string in `sameAs` | Block 2 |
| `areaServed` and `serviceArea` both set, duplicating each other | Block 2 |
| Locality and region swapped | Block 1 |
| `aggregateRating`, `image` array, `hasOfferCatalog`, `Service`, `FAQPage` missing | Almost all pages |
| `geo` precision (7 decimals) | Fine |
| Same business `@id` and Gillingham address on all 90 town pages, nothing town-specific | Town pages |

Ready-to-use consolidated block (confirm the phone number first):

```json
{
  "@context": "https://schema.org",
  "@type": ["AutoRepair", "LocalBusiness"],
  "@id": "https://unit11.co/#localbusiness",
  "name": "Unit-11",
  "legalName": "Unit Eleven Ltd",
  "url": "https://unit11.co/",
  "telephone": "+447360280307",
  "email": "bookings@unit11.co",
  "image": "https://unit11.co/wp-content/uploads/2023/03/iStock-1427639383-1536x1024.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Unit 11, Railway Street Industrial Estate, Railway Street",
    "addressLocality": "Gillingham",
    "addressRegion": "Kent",
    "postalCode": "ME7 1YQ",
    "addressCountry": "GB"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 51.3889089, "longitude": 0.5536614 },
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "09:00",
    "closes": "17:30"
  }],
  "hasMap": "https://www.google.com/maps?cid=13808659323212161400",
  "areaServed": [
    { "@type": "City", "name": "Gillingham" },
    { "@type": "City", "name": "Maidstone" },
    { "@type": "City", "name": "Rochester" }
  ],
  "sameAs": [
    "https://www.facebook.com/weareunit11/",
    "https://www.instagram.com/unit.eleven/",
    "https://www.youtube.com/@unit--11"
  ]
}
```

Add `aggregateRating` only once real, visible reviews exist on the page. Replace the `areaServed` list with the towns you genuinely serve.

## 6. Local links and authority (4/10)

- No visible Chamber of Commerce, BBB, local press, sponsorship or community signals on the pages reviewed.
- The portfolio page has only about 400 words, and project case studies (Jaguar E-Type, Cortina, VW Caddy) are the best local-proof content on the site but are not linked from town pages.
- Backlink counts, Domain Authority, and referring-domain quality are not measurable here.
- Brand mentions correlate roughly 3x more strongly with AI visibility than backlinks (Ahrefs, via the skill's data). The business has little verifiable third-party presence from open-web searches.
- Suggested benchmark from the skill: 5 to 10 quality local links per month.

## AI search impact (local)

- `/llms.txt` returns 404.
- robots.txt has no rules for AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended). Not blocking is fine, but there is no deliberate policy either.
- ChatGPT does not read GBP. It draws on the Bing index, Yelp, TripAdvisor, BBB and Reddit. With no Bing Places, Yelp or review-site presence found, this business is unlikely to be recommended in AI local answers.
- Run `/seo geo https://unit11.co` (if installed) for the full citability and brand-mention audit. The skill only recommends it, and the `seo-geo` skill is not installed in this project.

---

## Prioritised actions (top 10)

| # | Priority | Action |
|---|---|---|
| 1 | Critical | Make one phone number consistent on page, `tel:` link, schema and GBP |
| 2 | Critical | Triage the 90 town pages. Keep towns with real work and proof, rewrite them to well over 60% unique content, consolidate or 301 the rest into the Kent hub pages. Do not create more |
| 3 | Critical | Remove the ECU remap review text from all 50 ceramic coating pages |
| 4 | Critical | Merge the two schema entities into one `AutoRepair` entity, fix locality and region, hours, currency, `sameAs` and `contactPoint`. Use the block above |
| 5 | High | Start a review programme and show reviews on the site, with `aggregateRating` once real. Keep a steady cadence and never gate |
| 6 | High | Add a Google Map embed (lazy-loaded) and visible opening hours to the contact section and footer |
| 7 | High | Give the homepage a static H1 or subheading with the service and Gillingham/Kent. Add Gillingham to the title |
| 8 | Medium | Remove cart, checkout, account, thank-you, lottery, booking-step and `-old` URLs from the sitemap and `noindex` them |
| 9 | Medium | Claim Bing Places and Apple Business Connect, and list on Yell, Thomson Local, FreeIndex and the XPEL, Gyeon, Gtechniq and Feynlab installer locators with identical NAP |
| 10 | Medium | Consolidate the overlapping blog posts, merge duplicates into the strongest URL, and link surviving posts to the relevant service pages |

## Quick wins (this week)
1. Fix the phone number everywhere.
2. Delete the remap review text from the ceramic pages.
3. Add `tel:` and a map embed to the footer.
4. Fix the malformed Facebook `sameAs` URL and the empty `sameAs` entry.
5. Add alt text to the 10 empty images on the homepage.
6. Claim Bing Places and Apple Business Connect.
7. Remove utility URLs from the sitemap.

## Medium effort (this month)
1. Replace the dual schema with one correct block and add `Service` and `FAQPage` markup to service pages.
2. Rewrite the top 8 to 10 town pages with real jobs, photos, drive time and local FAQs.
3. Consolidate duplicate blog posts.
4. Start the review request process and publish reviews on site.
5. Submit to UK citation sources and manufacturer installer directories.
6. Add `llms.txt` and an explicit AI crawler policy.

## High impact (this quarter)
1. Decide the long-term town page strategy: a small set of genuinely local pages, linked from the Kent hubs, backed by case studies.
2. Local digital PR: aim for "best detailers in Kent" style lists, which are a top AI visibility citation factor.
3. Pursue local authority signals: Chamber of Commerce, Medway or Kent business awards, car club sponsorships and event coverage.
4. Publish project case studies with location data (client town, car, work done) and link them from the matching town pages.

## Limitations

This analysis could not assess: geo-grid or live local pack ranking, Domain Authority and the full backlink profile, GBP Insights, actual GBP categories, review count, rating and velocity, whether directory citations exist (searches were inconclusive), Core Web Vitals field data, or mobile rendering. The skill's two reference files were not present, so industry-specific schema and citation advice is general. Town-page duplication was measured exactly for 28 random pairs and by structure for the rest. Paid tools such as BrightLocal, Whitespark, Local Falcon, or the DataForSEO MCP (not connected here) can close the gaps.
