import os
import requests
import json
from dotenv import load_dotenv

# Load keys
ENV_PATH = "/home/agentrogue/cognarc/config/environments/.env.development"
load_dotenv(ENV_PATH)

def verify_supabase_anon():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key: return "❌ Missing keys"
    try:
        # Try health endpoint which doesn't always need auth, or auth/v1/settings
        resp = requests.get(f"{url}/auth/v1/health")
        if resp.status_code == 200:
            # Now try with key to see if key is accepted
            resp2 = requests.get(f"{url}/rest/v1/", headers={"apikey": key, "Authorization": f"Bearer {key}"})
            if resp2.status_code in [200, 204]: return "✅ Working"
            return f"⚠️ URL OK, but Key 401 (Body: {resp2.text[:50]})"
        return f"❌ URL Failed (Status: {resp.status_code})"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_supabase_service():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: return "❌ Missing keys"
    try:
        resp = requests.get(f"{url}/rest/v1/", headers={"apikey": key, "Authorization": f"Bearer {key}"})
        if resp.status_code in [200, 204]: return "✅ Working"
        return f"❌ Failed (Status: {resp.status_code}, Body: {resp.text[:50]})"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_mongodb():
    url = os.getenv("MONGODB_URL")
    if not url: return "❌ Missing key"
    try:
        from pymongo import MongoClient
        client = MongoClient(url, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return "✅ Working"
    except ImportError: return "⚠️ pymongo not installed"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key: return "❌ Missing key"
    try:
        resp = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        if resp.status_code == 200: return "✅ Working"
        return f"❌ Failed (Status: {resp.status_code})"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_upstash():
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token: return "❌ Missing keys"
    try:
        resp = requests.get(f"{url}/ping", headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200: return "✅ Working"
        return f"❌ Failed (Status: {resp.status_code})"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_vercel():
    token = os.getenv("VERCEL_TOKEN")
    if not token: return "❌ Missing key"
    try:
        resp = requests.get(
            "https://api.vercel.com/v2/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200: return "✅ Working"
        return f"❌ Failed (Status: {resp.status_code})"
    except Exception as e: return f"❌ Error: {str(e)}"

def verify_langfuse():
    host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    if not host or not pk or not sk: return "❌ Missing keys"
    try:
        import base64
        auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
        resp = requests.get(
            f"{host}/api/public/health",
            headers={"Authorization": f"Basic {auth}"}
        )
        if resp.status_code == 200: return "✅ Working"
        return f"❌ Failed (Status: {resp.status_code})"
    except Exception as e: return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    print("\n🔍 COGNARC Key Verification Report (Final)")
    print("="*40)
    print(f"Supabase (Anon):    {verify_supabase_anon()}")
    print(f"Supabase (Service): {verify_supabase_service()}")
    print(f"MongoDB:           {verify_mongodb()}")
    print(f"Groq:              {verify_groq()}")
    print(f"Upstash:           {verify_upstash()}")
    print(f"Vercel:            {verify_vercel()}")
    print(f"Langfuse:          {verify_langfuse()}")
    print("="*40)
