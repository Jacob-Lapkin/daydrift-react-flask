from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser
from typing import List
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType

load_dotenv()


# Define your desired data structure.
class DayDriftParser(BaseModel):
    title: str = Field(description="A fun and enthusiastic short title for the user's exercise adventure that will be shown to the user. This should be unique and relevant.")
    totalCalories: int = Field(description="The estimated total calories burned during the entirety of the exercise adventure. This should consider the duration and intensity of the workouts.")
    duration: int = Field(description="The duration of the exercise adventure in terms of minutes")
    waterQuantity: int = Field(description="The quantity of water that the user should drink during entirety of the adventure in milliliters")
    safetyPrecautions: str = Field('exercise-related safety tips that are relevant to their specific location.')
    adventureSubtitles: List = Field(description="List of adventure subtitles that give insights and highlights to what the step of the excercise adventure entails. List Length should should be the same length as adventures. Remember each subtitle should be an item in the list.")
    adventures: List = Field(description="List of steps in the excercise adventure. Each step should be 50 words")

# Set up a parser + inject instructions into the prompt template.
parser = PydanticOutputParser(pydantic_object=DayDriftParser)

class DayDrift:
    def __init__(self, location, duration, radius, intensity, text_temp=0.4, model='gpt-3.5-turbo'):
        self.location = location
        self.duration = duration
        self.radius = radius
        self.intensty = intensity
        self.text_temp = text_temp
        self.model = model
        self._drift = None
        self._drift_events = None

    def get_default_prompt(self):
        template = """
                    As an Exercise Adventure Assistant, you specialize in crafting location-specific exercise journeys. When designing, remember:

                    - Choose specific locations: parks, beaches, trails, etc
                    - Make steps detailed and distinct.
                    - Aim for diverse adventures.
                    - Each step in the exercise adventure should be described with roughly 50 words.
                    - Factor in calorie burn and safety.
                    - Adjust based on available time due to travel where each step should be geographically close to each other. 
                    - Steps should not require the user to travel by car to the next step so keep the distance small. 
                    - Most importatly, keep the number of locations to the user desired location count.
                    Craft the exercise adventure following these guidelines: {format_instructions}

                    Please design an exercise adventure in {location} for a duration of {duration} hours within a {radius}-mile radius with an intensity level of {intensity} out of 100
                    where 100 is maximum calories burned. Provide a step-by-step guide, with each step leading to different places within the radius.
                    """
        self._drift = template
        return template
    
    def create_drift(self):
        
        template = self.get_default_prompt()
        
        llm = ChatOpenAI(temperature=self.text_temp, max_tokens=2000, model_name=self.model)

        prompt = PromptTemplate(template=template,
                                input_variables=['location', 'duration', 'radius', 'intensity'], 
                                partial_variables={"format_instructions": parser.get_format_instructions()}
                                )
        _input = prompt.format_prompt(location=self.location, duration=self.duration, radius=self.radius, intensity = self.intensty)
        
        output = llm(_input.to_messages())
        parsed_output = parser.parse(output.content)
        return parsed_output
    
    

# exercise_test = DayDrift(location="Sydney, Australia", duration=1, radius=1, intensity=99)

# print(exercise_test.create_drift())
