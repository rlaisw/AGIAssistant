# Data Model: Welcome Feature Cards

No persistence, no entities — one static array of six records rendered by
the existing empty state.

## `FEATURE_CARDS` record shape

```text
{ title: string, icon: string (emoji), description: string,
  label: string, url: string }
```

## The six records (locked, in render order)

| # | title | icon | description | label (= the prompt sent on body click) | url |
|---|---|---|---|---|---|
| 1 | Generate PowerPoint | 📊 | Create professional PowerPoint from text prompts in minutes | How to create PPT | http://localhost/example1.html |
| 2 | Generate Infographic | 🎨 | Design eye-catching infographics without design skills | How to create Infographic | http://localhost/example2.html |
| 3 | Draw Chart Diagram | 📈 | Visualize data with interactive charts and flow diagrams | How to create chart diagram | http://localhost/example3.html |
| 4 | Talk with CorpIT Helpdesk Chatbot | 💻 | Get instant IT support and troubleshooting guidance | Chat with CorpIT Support | http://localhost/example4.html |
| 5 | Ask Any Question with AI Chatbot | 🤖 | Access knowledge across domains with our intelligent assistant | Ask AI Chatbot | http://localhost/example5.html |
| 6 | Create Personal Agentic RAG Document DB | 💾 | Build your own searchable knowledge base with AI-powered Agentic RAG | Create Self-Hosted Agentic RAG | http://localhost/example6.html |

Validation rule: the array renders in order; label text is both the sent
prompt and the link's visible text; URLs are the temporary placeholders
until real help pages exist.
