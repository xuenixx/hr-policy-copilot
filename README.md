# HR Policy Copilot

A RAG-based HR policy assistant for Singapore employers, built with Claude API and ChromaDB.

## What it does
Answers HR policy questions with cited sources, based on Singapore's Employment Act and Tripartite Guidelines.

## Sample questions it can answer
- What is the notice period for termination?
- How many days of sick leave is an employee entitled to?
- What retrenchment benefits should an employer pay?
- Can an employer reject a flexible work arrangement request?
- What counts as wrongful dismissal in Singapore?

## Tech stack
- Python
- Anthropic Claude API (claude-haiku-4-5)
- ChromaDB (vector database)
- PyPDF2 + PyMuPDF (PDF extraction)
- Google Colab

## Data sources
Singapore Ministry of Manpower and Tripartite Alliance guidelines including Employment Act 1968, Wrongful Dismissal Guidelines, FWA Guidelines, Retrenchment Advisory, and Workplace Harassment Advisory.

## Known limitations
- Requires Google Colab session to run
- ChromaDB resets on session restart
- Some scanned PDFs not extractable via PyPDF2
