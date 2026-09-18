import urllib.request
import urllib.error
import json
import sys

def run_test():
    base_url = "http://127.0.0.1:8000"
    
    # Create session
    print("--- STARTING NEW SESSION ---")
    try:
        req = urllib.request.Request(f"{base_url}/api/session", method="POST")
        with urllib.request.urlopen(req, timeout=10.0) as response:
            if response.status != 200:
                print("Failed to create session:", response.read().decode())
                return
            session = json.loads(response.read().decode())
            session_id = session["session_id"]
            print(f"Session created: {session_id}\n")
    except Exception as e:
        print("Error connecting to server:", e)
        return
    
    # Helper to send message
    def send_message(msg):
        print(f"User: {msg}")
        try:
            data = json.dumps({"session_id": session_id, "message": msg}).encode()
            req = urllib.request.Request(f"{base_url}/api/chat", data=data, method="POST")
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=30.0) as response:
                if response.status != 200:
                    print(f"API Error (Status {response.status}): {response.read().decode()}\n")
                    return None
                data = json.loads(response.read().decode())
                print(f"Assistant: {data['assistant_message']}")
                print("Current State (Important Fields Only):")
                state = data['state']
                
                # Print state clearly
                print(f"  full_name: {state.get('full_name')}")
                print(f"  home_address: {state.get('home_address')}")
                print(f"  covers_worldwide_assets: {state.get('covers_worldwide_assets')}")
                print(f"  has_children: {state.get('has_children')}")
                print(f"  children_names: {state.get('children_names')}")
                print(f"  executor: {state.get('executor')}")
                print(f"  specific_gifts: {state.get('specific_gifts')}")
                print(f"  additional_wishes: {state.get('additional_wishes')}\n")
                
                return data
        except urllib.error.HTTPError as e:
            print(f"API Error (Status {e.code}): {e.read().decode()}\n")
            return None
        except Exception as e:
            print(f"Request failed: {e}\n")
            return None

    # Scenario A: Normal conversation
    send_message("My name is John Smith.")
    send_message("I live at 10 Main Street.")
    send_message("Yes, it covers worldwide assets.")
    send_message("I have two children.")
    send_message("Their names are Sarah and Michael.")
    send_message("My executor is my brother James.")
    send_message("I want to give my car to Sarah.")
    send_message("No additional wishes.")

if __name__ == "__main__":
    run_test()
