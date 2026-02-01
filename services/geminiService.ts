
import { GoogleGenAI, Type } from "@google/genai";
import { Task, MorningBriefing } from "../types";

/**
 * Generates a personalized morning briefing based on today's pending tasks.
 * Uses Gemini 3 Flash for efficient, high-quality reasoning.
 */
export async function generateMorningBriefing(tasks: Task[]): Promise<MorningBriefing> {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const taskListText = tasks.length > 0 
    ? tasks.map(t => `- ${t.title} (Priority: ${t.priority})`).join('\n')
    : "No major tasks scheduled for today.";

  const prompt = `
    You are a wise, calming, and highly productive life coach. 
    It is early morning. Help the user start their day with focus and positivity.
    
    Current Tasks for Today:
    ${taskListText}
    
    Please generate:
    1. A beautiful, inspiring, and unique morning quote.
    2. A short personalized "Zen Message" (2-3 sentences) summarizing the day's vibe and offering encouragement based on their tasks.
    3. A few "Strategic Action Items" (2-3) which might be creative ways to approach their list or self-care tips.
    
    Return the response strictly as JSON.
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            quote: { type: Type.STRING },
            author: { type: Type.STRING },
            message: { type: Type.STRING },
            actionItems: { 
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          },
          required: ["quote", "author", "message", "actionItems"]
        }
      }
    });

    const data = JSON.parse(response.text || '{}');
    return {
      quote: data.quote || "The sun rises every day, offering a new chance to begin.",
      author: data.author || "Traditional Zen Saying",
      message: data.message || "Take a deep breath. Today is a clean slate for your ambitions.",
      actionItems: data.actionItems || ["Start with your most challenging task first.", "Take five minutes to meditate before beginning work."],
      generatedAt: Date.now()
    };
  } catch (error) {
    console.error("Error generating Gemini briefing:", error);
    // Fallback data
    return {
      quote: "Success is not final, failure is not fatal: it is the courage to continue that counts.",
      author: "Winston Churchill",
      message: "An error occurred generating your personalized briefing, but your path remains clear.",
      actionItems: ["Review your list manually.", "Take a deep breath and start with step one."],
      generatedAt: Date.now()
    };
  }
}
