# Agent Team — Sales & Marketing

## Roles

### 🎯 Seller Agent
- **Job:** Cold outreach, follow-ups, closing deals
- **Model:** xiaomi/mimo-v2.5-pro (needs good reasoning for sales)
- **Tools:** Email (SMTP via max@hd-webdesign.si), lead CSVs
- **KPI:** Replies received, demos booked, sales closed
- **Daily:** Check replies, send follow-ups, draft new outreach

### 📢 Promoter Agent  
- **Job:** Social media content, Facebook group posts, community engagement
- **Model:** openrouter/google/gemma-4-26b-a4b-it:free (content creation is simple)
- **Tools:** Web search, content templates
- **KPI:** Posts created, engagement potential
- **Daily:** Create 2-3 social media posts, find new groups

### ✍️ Content Agent
- **Job:** Blog posts, email templates, landing page copy
- **Model:** openrouter/google/gemma-4-26b-a4b-it:free
- **Tools:** File system (write to workspace)
- **KPI:** Posts published, quality score
- **Daily:** Write 1-2 blog posts or marketing materials

### 🔍 Lead Scout
- **Job:** Find new restaurant and agency leads continuously
- **Model:** openrouter/google/gemma-4-26b-a4b-it:free
- **Tools:** Web search, CSV files
- **KPI:** New leads found per day
- **Daily:** Find 10-20 new qualified leads with emails

### 📊 Analytics Agent
- **Job:** Track metrics, monitor email replies, report on performance
- **Model:** openrouter/google/gemma-4-26b-a4b-it:free
- **Tools:** File system, web fetch
- **KPI:** Reports delivered on time
- **Daily:** Check email replies, update lead status, daily report

## Communication
- All agents write results to `/workspace/agents/outputs/`
- Seller agent reads from lead CSVs in `/workspace/lead-gen/`
- Max (main agent) orchestrates and reviews before any external action
