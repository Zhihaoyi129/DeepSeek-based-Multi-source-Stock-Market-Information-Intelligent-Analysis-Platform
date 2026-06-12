# Multi-source Stock Market Information Intelligent Analysis Platform Based on DeepSeek 
## Development Tools: 
- Pycharm (Code Writing) 
## Development Languages and: 
- Python (implemented web pages using Flask) 
## List of Components: 
- No hardware
## Original Requirements 

Based on DeepSeek's multi-source stock market information intelligent analysis platform
Title and division suggestions (each person is responsible for one module)
1. : Based on DeepSeek's multi-source stock market information intelligent analysis platform - News and Policy Text Sentiment Analysis Module
Task: Use DeepSeek to conduct text understanding and sentiment analysis of financial news, policy documents, and company announcements
Technology stack: DeepSeek API, text preprocessing, sentiment classification model (can be fine-tuned with pre-trained models)
2. : Based on DeepSeek's multi-source stock market information intelligent analysis platform - Technical Indicators and Trading Data Visualization Module
Task: Responsible for obtaining stock trading data, calculating technical indicators (MA, RSI, etc.), and generating visual charts
Technology stack: Python (pandas, matplotlib/yfinance), data interfaces (such as AKShare, Tushare)
3. : Based on DeepSeek's multi-source stock market information intelligent analysis platform - Multi-source Data Fusion and Decision Recommendation Generation Module
Task: Merge the analysis results of news with technical indicator data, and use DeepSeek to generate comprehensive trading recommendations
Technology stack: LangChain (optional), Prompt Engineering, Decision Logic Design
4. : Based on DeepSeek's multi-source stock market information intelligent analysis platform - System Integration and Web Interface Development
Task: Build front-end and back-end systems, integrate the functions of each module, and provide a user interaction interface
Technology stack: Flask/Django + Vue/React, system deployment and testing 

## Overall Function/Requirement: 
System Integration and Web Interface Development 
The overall web pages of the system are implemented using Flask, while the DeepSeek part interacts through interface calls. 2.

News and Policy Text Sentiment Analysis Module (Page 1) 
By using the conversation method, the text-based news and policy information is pasted into the chat. The system calls DeepSeek through the interface and then returns the results. 
Technical Indicators and Trading Data Visualization Module (Page 2) 
By specifying the transaction data to be retrieved in the dialog box, the system calls the visualization module to perform data visualization. The data is obtained through akshare or tushare. 
Multi-source Data Fusion and Decision Recommendation Generation Module (Page 3) 
If:
Emotion = Positive
And RSI < 70
And Price > MA5
→ Recommendation: Buy 
If:
Emotion = Negative
Or RSI > 70
→ Recommendation: Sell 
Otherwise:
→ Wait and see 

## Overall Function Enhancement:
1. A new scheduled task module has been added. A front-end page for managing scheduled tasks has been created, allowing for setting the frequency and content of the tasks (with preset task content).
2. A preset task for automatically obtaining news has been added.
