Here are some ideas for a female-friendly job search prototype, ranging from core features to differentiating ones:

**Core concept: personalized, context-aware job matching**

The app goes beyond keyword matching. A female candidate enters her interests, skills, experience level, and career goals — and the app uses that profile to fetch and rank real job listings from the web, filtered through lenses that matter specifically to women.

Here's a mockup of what the experience could look like:Here's a breakdown of the key ideas across different dimensions:

**Female-specific filters (the differentiator)**

The filters that matter most to women aren't available on standard job boards. The app could surface things like pay transparency ratings, parental leave policy length, percentage of women in leadership or engineering, return-to-work and career gap-friendly programs, and flexible/async work culture indicators. These get pulled from job postings, company reviews, and public DEI reports in real time.

**Profile input that goes beyond a resume**

Rather than uploading a CV, users answer a short set of questions: skills and interests, career stage, workplace priorities (mentorship, flexibility, pay equity, growth), and whether they're returning from a career break. This richer input drives much better matching than keyword search alone.

**Workplace culture intelligence**

The app could use web search to pull public data on each company — Glassdoor gender scores, LinkedIn leadership gender ratios, press mentions of DEI commitments or controversies, and parental leave benchmarks. This gives candidates a quick "culture snapshot" before applying, saving time researching companies separately.

**Career gap normalization**

A dedicated mode for women returning to work after a career break (for caregiving, health, relocation, etc.). The app finds companies with formal return-to-work programs, can reframe skills from non-traditional experience, and surfaces roles that explicitly welcome career restarters.

**Salary confidence tools**

Since women are statistically more likely to undervalue themselves in salary negotiations, the app could show market rate ranges by role, location, and years of experience, and surface only companies that publicly post salary bands — removing the information asymmetry before the first interview.

**Mentor and community layer**

Beyond job listings, the app could connect users with women already working at target companies (via LinkedIn or a community network), recommend women-focused Slack communities or professional networks by industry, and provide tailored interview prep for bias-heavy question types.

**Technical architecture idea**

The prototype could be built as a Claude-powered Artifact: the user fills in a profile form, the app calls the Anthropic API with that profile as context, and Claude performs web searches to find real job listings and company culture data, then synthesizes everything into ranked recommendations with explanations. This would be a very buildable v1.