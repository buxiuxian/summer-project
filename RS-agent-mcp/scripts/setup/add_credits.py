#!/usr/bin/env python3
"""
RSHub Credit Top-up Script
可靠的充值脚本，避免批处理文件的转义问题
"""

import requests
import json
import os
import sys

def add_credits(token, credits_amount):
    """添加credit到指定token"""
    url = "https://rshub.zju.edu.cn/api/Update-credits"
    data = {"token": token, "credits": credits_amount}
    
    try:
        print(f"Adding {credits_amount} credits to token...")
        print(f"Token: {token}")
        print(f"Sending request to: {url}")
        
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result", False):
                print(f"✅ Success! Credits added successfully.")
                print(f"💰 New balance: {result.get('credits', 'Unknown')} credits")
                return True
            else:
                print(f"❌ Failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def check_credits(token):
    """检查当前credit余额"""
    url = "https://rshub.zju.edu.cn/api/Check-credits"
    data = {"token": token, "credits": 0}
    
    try:
        print("Checking current balance...")
        
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            current_credits = result.get("credits", 0)
            print(f"💰 Current balance: {current_credits} credits")
            return current_credits
        else:
            print(f"❌ Failed to check balance: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """主函数"""
    print("RSHub Credit Top-up Script")
    print("=" * 40)
    
    # 获取token
    token = os.environ.get('RSHUB_TOKEN')
    if not token:
        print("❌ Error: RSHUB_TOKEN environment variable not set")
        print("Please set it first, example:")
        print("set RSHUB_TOKEN=your_token_here")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # 检查当前余额
    current_balance = check_credits(token)
    
    # 添加1000个credit
    credits_to_add = 1000
    print(f"\n{'='*40}")
    
    if add_credits(token, credits_to_add):
        print("\n🎉 Credit top-up completed successfully!")
        
        # 再次检查余额确认
        print("\nVerifying new balance...")
        check_credits(token)
    else:
        print("\n😞 Credit top-up failed!")
    
    print("\n" + "=" * 40)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 