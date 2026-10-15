# Local SEO Analysis: unit11.co

Audit date: 2026-10-15. Method: homepage, contact page, robots.txt, sitemaps and a sample of four location pages fetched and parsed. No GBP, citation or ranking tools were available.

## Local SEO Score: 52/100

| Dimension | Weight | Score | Notes |
|---|---|---|---|
| GBP signals | 25% | 15/25 | Maps CID in schema `hasMap`, but no embed, hours or category cues on page |
| Reviews and reputation | 20% | 3/20 | No review count, rating, testimonials or `aggregateRating` found |
| Local on-page | 20% | 8/20 | Good city/service titles, but about 90 near-identical location pages |
| NAP and citations | 15% | 9/15 | NAP present, but inconsistent across sources |
| Local schema | 10% | 7/10 | Rich but duplicated, with errors |
| Local links and authority | 10% | 4/10 | Few visible authority signals |
| Rounded total | | 46 base, 52 after credit for dedicated service pages and crawl health | |

Note: the table total is a judgement call. The weighted dimension scores sum to 46, and I added 6 for strong service-page coverage, clean robots.txt and sitemap, and a canonical tag.

## Business type

Hybrid, leaning brick-and-mortar. There is a real unit address (Unit 11, Railway Street Industrial Estate, Gillingham ME7 1YQ) plus a 20 km service-area circle in schema and many "ceramic coating in [town]" pages for places the business visits or serves.

## Industry vertical

Automotive services (detailing, PPF, ceramic coating, restoration, servicing, ECU remapping). The skill's automotive path is geared to dealerships, so I applied the generic `LocalBusiness` path with `AutoRepair`/`AutomotiveBusiness` as the better subtype.

## GBP optimisation checklist

| Signal | Status |
|---|---|
| GBP reference in schema (`hasMap` with CID 13808659323212161400) | Present, but only in schema |
| Embedded Google Map on page | Not found (only a booking form iframe) |
| Opening hours visible on page | Not found in body text. Only in schema as free text |
| Reviews widget | Missing |
| Social profiles linked | Facebook, Instagram, YouTube, TikTok (footer) |
| Click-to-call (`tel:`) | Present: `tel:07360280307` |
| Q&A / FAQ content to replace deprecated GBP Q&A | Not seen on homepage |

Actions: confirm the primary category is "Car detailing service" (or the strongest revenue service) with secondary categories for PPF, ceramic coating and restoration. Do not point the GBP link at the homepage if it competes with a stronger organic page.

## Review health snapshot

No visible review count, rating, testimonial block or third-party review badge on the homepage, and no `aggregateRating` in any schema block. This is the biggest gap for a business competing in a map pack. Review velocity (the 18-day rule) cannot be measured from the site. Check it in GBP directly.

## NAP consistency audit

| Source | Name | Address | Phone |
|---|---|---|---|
| Footer / page | Unit-11 (and "Unit Eleven Ltd") | Unit 11 Railway Street Industrial Estate, Railway Street, Gillingham, Kent, ME7 1YQ | 07360 280307 |
| Schema block 1 (Rank Math graph) | UNIT-11 | 11, Railway Street Industrial Estate; locality "Railway St"; region "Gillingham" | +44 3333 058378 |
| Schema block 2 (hand-written LocalBusiness) | UNIT-11 | Street includes "Railway St"; locality "Gillingham"; region "Kent" | +44 3333 058378 |

Findings (Critical):
1. **Phone mismatch.** Visible and `tel:` number is 07360 280307. Both schema blocks say +44 3333 058378. Pick one primary number and align everything, including GBP.
2. **Address field errors in schema block 1.** `addressLocality` is "Railway St" and `addressRegion` is "Gillingham". Locality should be Gillingham and region Kent.
3. **Two competing LocalBusiness/Organization entities** with different `@id` values (`https://unit11.co/#organization` and `https://unit11.co`) and different emails (bookings@ vs hello@).
4. **Name variants:** UNIT-11, Unit-11, Unit 11, Unit Eleven Ltd.

## Citation presence check

Not verifiable from this environment (no `site:` search). Recommended checks: Yelp, BBB, Facebook (linked, but the schema `sameAs` has a malformed entry `https://facebook.com/@weareunit11`), Bing Places, Apple Business Connect, Checkatrade, Thomson Local, Yell, and detailing/PPF directories (XPEL installer locator, Gyeon and Gtechniq certified-installer pages). Submit to Data Axle, Foursquare and Neustar/TransUnion equivalents for the UK.

## Local schema status

Present on all sampled pages, which is good, but needs cleanup:
- Duplicate blocks (Rank Math Place/Organization graph plus a custom LocalBusiness).
- Block 2 problems: `openingHours` is free text ("Open from Monday to Friday...") and should be `openingHoursSpecification` with Mo-Fr 09:00-17:30; `additionalProperty` is a URL string where a `PropertyValue` is expected; `currenciesAccepted` is "$" and should be "GBP"; `priceRange` "100-10000" is not a conventional value; `ContactPoint` is capitalised as a property name instead of `contactPoint`; `sameAs` contains an empty string; `serviceArea` and `areaServed` duplicate each other.
- `geo` has 7 decimals, which meets the 5-decimal minimum.
- Missing: `aggregateRating`, `image` array, `hasOfferCatalog`, `branchOf` or parent link, and an automotive subtype (`AutoRepair` or `AutomotiveBusiness`).
- Every location page repeats the same Gillingham LocalBusiness with the same `@id`, with no town-specific data. That is expected for an SAB, but it adds no local relevance.

Ready-to-use fix (sketch):

```json
{
  "@context": "https://schema.org",
  "@type": ["AutoRepair", "LocalBusiness"],
  "@id": "https://unit11.co/#localbusiness",
  "name": "Unit-11",
  "url": "https://unit11.co/",
  "telephone": "+447360280307",
  "email": "bookings@unit11.co",
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
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens": "09:00", "closes": "17:30"
  }],
  "hasMap": "https://www.google.com/maps?cid=13808659323212161400",
  "sameAs": ["https://www.facebook.com/weareunit11/", "https://www.instagram.com/unit.eleven/", "https://www.youtube.com/@unit--11"]
}
```

Confirm the phone number to use before publishing.

## Location page quality (multi-location)

Sitemap contains **50 `ceramic-coating-in-{town}` pages and 40 `paint-protection-film-{town}` pages (about 90 in total)**, covering towns from Kent into Essex and south and east London (e.g. Tilbury, Brentwood, Romford, Walthamstow, Croydon).

Swap test results (town name replaced, remaining text compared):
- Ceramic coating, Orpington vs Canterbury: **99.3% identical** (2,150 vs 2,148 words).
- PPF, Maidstone vs Dartford: **89.7% identical** (1,875 vs 1,873 words).

This is far below the 60-70% unique content guideline and matches the doorway pattern in the skill (swap the city and it still reads the same). The pages also repeat identical H1/H2 phrasing, identical schema, and no local photos, testimonials, drive-time or landmark detail were seen. Many served towns are 30 to 60 miles from Gillingham, outside the declared 20 km radius, so the pages also contradict the site's own `serviceArea`.

Skill quality gate: with 50+ location pages this is a **HARD STOP** condition for creating or expanding location pages. No new pages should be generated without a written justification. Recommended path: keep only towns inside a realistic service radius where you have real proof (jobs, customers, photos), rewrite those to be more than 60% unique, and consolidate or `noindex`/301 the rest into the Kent hub pages (`/ceramic-coating-kent/`, `/paint-protection-film-kent` equivalents). March 2024 Core Update case studies show 60-80% ranking losses for this pattern.

Other observations:
- Legacy URLs in the sitemap (`classic-car-restoration-old`, `foundation-detail-old`, `correction-detail-old`, `contact-us-2`, `services-1`, `services-2`) and transactional pages (cart, checkout, my-account, dashboard, thank-you pages, lottery pages) are indexable in the sitemap. Remove them from the sitemap and `noindex` where appropriate.
- Homepage H1 is an animated rotating headline ("From Servicing / Tuning / Detailing / Restoring to Perfection") with no city term. Title tag does have "Kent" but not Gillingham.
- 10 of 11 images on the homepage have empty alt text.
- Footer copyright reads 2023-2025 in one place and 2024 in another.

## Top 10 prioritised actions

1. **Critical:** Make the phone number identical on page, `tel:` link, both schema blocks and GBP.
2. **Critical:** Triage the ~90 near-duplicate location pages: keep, rewrite or consolidate (per the quality gate above). Do not add more.
3. **Critical:** Merge the two schema entities into one `LocalBusiness`/`AutoRepair` with one `@id`, and fix locality, region, hours, currency and `sameAs` errors.
4. **High:** Build a review programme and show reviews on site (Google rating widget plus `aggregateRating` only if it matches real, visible reviews). Keep a steady cadence, avoiding review gating.
5. **High:** Add a visible Google Map embed and opening hours to the contact section and footer.
6. **High:** Add "Gillingham" and the primary service to the homepage title and a static H1 or subheading.
7. **Medium:** Remove cart, checkout, account, thank-you, lottery and `-old` URLs from the sitemap; `noindex` them.
8. **Medium:** Claim and complete Bing Places and Apple Business Connect; verify Yell, Checkatrade and XPEL/Gyeon/Gtechniq installer listings use the same NAP.
9. **Medium:** Write unique service-area content for the top 5 to 8 towns (real jobs, photos, local FAQs) instead of 90 templates.
10. **Low:** Add alt text to images, fix the Facebook `sameAs` URL, and align the footer copyright and company name ("Unit-11" vs "Unit Eleven Ltd" vs "Unit 11").

## Limitations

This analysis could not assess: geo-grid or live local pack rankings, Domain Authority and the full backlink profile, GBP Insights, actual GBP category, review count, rating and velocity, citation presence on third-party directories, or Core Web Vitals. Paid tools (e.g. BrightLocal, Whitespark, Local Falcon, DataForSEO) can fill these gaps. The skill's two reference files (`local-seo-signals.md`, `local-schema-types.md`) were not available, so industry-specific schema and citation guidance is based on general knowledge. Only a sample of four location pages was compared, so the duplication rate for the other pages is inferred.
