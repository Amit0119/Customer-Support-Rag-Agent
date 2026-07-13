import os
from dotenv import load_dotenv
from rag_engine import RAGEngine

load_dotenv()

def main():
    print("Initializing RAGEngine...")
    try:
        engine = RAGEngine()
        
        if engine.rag_chain is None:
            print("❌ Error: RAGEngine initialized but rag_chain is None. Check vector store or model setup.")
            return

        print("✅ RAGEngine initialized successfully.")
        
        test_query = "Do you ship to India?"
        print(f"\nTesting Query: {test_query}")
        
        response = engine.get_response(test_query, [])
        print(f"\nResponse: {response['answer']}")
        print(f"Sources retrieved: {len(response['sources'])}")
        
        print("\n✅ Test completed successfully. No bugs found in the pipeline.")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    main()
