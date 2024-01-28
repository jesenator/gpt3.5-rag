import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html2text
import openai


chat_content = '''
You are an intelligent AI assistant who is allowed to search the internet.
A user will ask you a question in the form of "Question: [the question]"
If you require an internet search to answer a user's question respond with:

"Search: [search query you require]" 
you will automatically be returned with Google search results to your query after the statement "Results: ".

Or you can search an exact webpage with:
"Search URL: [URL you require]"
You will be returned the text on that webpage

You can search as many times as necessary to learn the information you desire.
Finally, when you have an answer to the original user-asked question say "Answer: [your answer]".

Only give the answer once you have searched the information you require to give the correct answer. 
Begin lines only with "Seach: ", "Search URL: ", or "Answer: "

Remember, although you don't have ingrained access to the internet saying "Search: " allows you to search for information from the current internet. You can search more than once if required.

Question: what time is it?

Search: what time is it now?

Results: "VerbatimLexington, MA / Local Time10:50 PMSaturday, January 28, 2023
Time in Lexington, MATime.istime.isYour clock is 2 minutes and 17.6 seconds behind. Accuracy of synchronization was ±0.005 seconds. Time in New York, United States now: 10:02:23pm.Exact time, any time zoneEastern TimeTime in United States nowCentral Time
"

Answer: the time is 10:50PM on Saturday, January 28th, 2023 in Lexington, MA

'''

def get_results(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    if url.find("https://www.google.com/search?q=") > 0:
        text = text[text.find("Verbatim"):text.find("People also ask")]
    if len(text) > 1500:
        text = text[:1500]

    return text


def generate_response(text):
  openai.api_key = ""

  response = openai.Completion.create(
    model="text-davinci-003",
    prompt=text,
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=["Results: "]
  )

  message = response.choices[0].text
  return message.strip()


def get_question(chat_content):
    question = "DEBUG"
    while question != "DEBUG":
        question = input("Enter your question: ")
        if question == "DEBUG":
            print(chat_content)
    chat_content += "Question: " + question + "\n\n"
    return chat_content


if __name__ == '__main__':
    chat_content = get_question(chat_content)

    for i in range(100):
        response = generate_response(chat_content)

        if response.find("Search: ") != -1:
            query = response[response.find("Search: ") + 8:]
            print(" *** searching: " + query)
            url = "https://www.google.com/search?q=" + query.replace(" ", "+")
          
            results = get_results(url)
            print(" *** processing results")
            chat_content += "Search: " + query + "\n\nResults: " + results + "\n\n"
          
        elif response.find("Search URL: ") != -1:  # TODO: finish
            query = response[response.find("Search URL: ") + 12:]
            url = query
            print(" *** searching URL: " + query)
          
            results = get_results(url)
            print(" *** processing results")
            print("===============Results: \n" + results + "\n==========")
            chat_content += "Search URL: " + query + "\n\nResults: " + results + "\n\n"
          
        elif response.find("Answer: ") != -1:
            answer = response[response.find("Answer: "):]
            print(answer)
            chat_content += answer + "\n\n"
            chat_content = get_question(chat_content)
        else:
            chat_content += "\n\n remember to start every query with \"Search: \" or \"Answer: \""
