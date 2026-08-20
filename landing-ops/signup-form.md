# Signup / Intake Form (Gumroad provisioning)

This form is used to collect information for onboarding pilots and Gumroad-based subscriptions across four apps: EtsyBooster, SEOBooster, MenuBoost, and GEOBoost.

## Form fields
- App interest: EtsyBooster | SEOBooster | MenuBoost | GEOBoost (dropdown)
- Company name
- Contact person
- Email address
- Role / title
- Website
- Use-case summary (short description of problem and goal)
- Current platform (e.g., Etsy, Wordpress, Shopify, none)
- Team size
- Estimated monthly budget (USD)
- Desired start date
- Preferred language for onboarding
- Timezone
- Agreement: I agree to Gumroad terms and onboarding flow

## Flow after submission
- User is redirected to the selected Gumroad product page for purchase (monthly or annual).
- After purchase, a Gumroad webhook triggers onboarding: account creation, pilot assignment, and access provisioning for the four apps according to the chosen plan.
- A welcome email with onboarding steps is sent automatically.

## Notes
- Use this form as a single intake for pilots to simplify the funnel and enable rapid testing.
- You can customize fields per-app if needed in the future.