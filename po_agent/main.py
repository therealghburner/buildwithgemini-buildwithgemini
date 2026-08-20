import os
import sys
from agent import build_po_agent_graph

def run_query(query_text: str, agent=None):
    if agent is None:
        agent = build_po_agent_graph()

    initial_state = {
        "user_query": query_text,
        "schema_info": "",
        "generated_sql": None,
        "query_result": None,
        "error_message": None,
        "retry_count": 0,
        "final_answer": None,
        "messages": []
    }

    result = agent.invoke(initial_state)
    return result

def main():
    if not os.path.exists("purchase_orders.db"):
        print("Database 'purchase_orders.db' not found. Generating dataset...")
        import generate_db
        generate_db.init_db()

    agent = build_po_agent_graph()

    print("==================================================================")
    print("      READ-ONLY PURCHASE ORDER AGENT (LangGraph Powered)          ")
    print("==================================================================")
    print("Sample Questions:")
    print("  1. What are the top 5 vendors by total spend?")
    print("  2. Show summary of PO statuses by department.")
    print("  3. List all pending POs over $50,000 ordered in the last 6 months.")
    print("  Type 'exit' or 'quit' to stop.\n")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}")
        result = run_query(query, agent)
        print("\n------------------- Executed SQL -------------------")
        print(result.get("generated_sql"))
        print("\n------------------- Agent Insights -------------------")
        print(result.get("final_answer"))
        return

    while True:
        try:
            user_input = input("\n[PO Agent Query] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting PO Agent. Goodbye!")
                break

            print("\nProcessing request through LangGraph pipeline...")
            result = run_query(user_input, agent)

            print("\n------------------- Executed SQL -------------------")
            print(result.get("generated_sql"))

            print("\n------------------- Agent Insights -------------------")
            print(result.get("final_answer"))

        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break
        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    main()
