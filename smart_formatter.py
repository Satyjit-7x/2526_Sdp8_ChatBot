import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

class SmartFormatter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def format_response(self, user_question, bot_response):
        """Smart formatting based on response type"""
        
        if not self.model:
            return self._quick_format(bot_response)
        
        # Detect response type and format accordingly
        if self._is_order_list(bot_response):
            return self._format_orders(bot_response)
        elif self._is_single_order(bot_response):
            return self._format_single_order(bot_response)
        elif self._is_order_creation(bot_response):
            return self._format_order_creation(bot_response)
        elif self._is_confirmation(bot_response):
            return self._format_confirmation(bot_response)
        elif self._is_clarification(bot_response):
            return self._format_clarification(bot_response)
        else:
            return self._format_general(user_question, bot_response)
    
    def _is_order_list(self, response):
        return ("orders:" in response.lower() or 
                ("•" in response and "ord" in response.lower()) or
                "total orders" in response.lower() or
                ("order" in response.lower() and "•" in response) or
                len(re.findall(r'ord\d+', response, re.IGNORECASE)) > 1)
    
    def _is_single_order(self, response):
        # Check if response contains order info and is about a single order
        has_order = bool(re.search(r'ord\d+', response, re.IGNORECASE))
        is_single = len(re.findall(r'ord\d+', response, re.IGNORECASE)) <= 1
        has_status = any(word in response.lower() for word in ["status", "delivered", "pending", "shipped", "returned", "cancelled"])
        
        return (has_order and is_single) or (has_order and has_status)
    
    def _is_confirmation(self, response):
        return "are you sure" in response.lower() or "confirm" in response.lower() or "yes" in response.lower() and "no" in response.lower()
    
    def _is_order_creation(self, response):
        return "create" in response.lower() or "add" in response.lower() or "insert" in response.lower() or "operation completed" in response.lower()
    
    def _is_clarification(self, response):
        return "which one" in response.lower() or "specify" in response.lower()
    
    def _format_orders(self, response):
        """Format order lists concisely - one order per line"""
        lines = []
        
        # Split by common delimiters and look for order patterns
        sections = re.split(r'[•\n]', response)
        
        for section in sections:
            section = section.strip()
            if not section or 'ord' not in section.lower():
                continue
                
            # Extract order ID
            order_match = re.search(r'(ord\d+)', section, re.IGNORECASE)
            if not order_match:
                continue
                
            order_id = order_match.group(1).upper()
            
            # Extract product name (before parenthesis)
            if '(' in section:
                product_part = section.split('(')[0].strip()
            else:
                product_part = section.split(order_id)[0].strip()
            
            # Clean product name
            product = product_part.replace('•', '').replace('-', '').strip()
            product = ' '.join(product.split())  # Remove extra spaces
            
            # Extract status
            status = "Unknown"
            if "delivered" in section.lower():
                status = "Delivered"
            elif "pending" in section.lower():
                status = "Pending"
            elif "returned" in section.lower():
                status = "Returned"
            elif "shipped" in section.lower():
                status = "Shipped"
            elif "cancelled" in section.lower():
                status = "Cancelled"
            
            # Format: OrderID: Product - Status
            if product and product != order_id:
                lines.append(f"• {order_id}: {product} - {status}")
            else:
                lines.append(f"• {order_id} - {status}")
        
        return '\n'.join(lines) if lines else self._quick_format(response)
    
    def _format_single_order(self, response):
        """Format single order status with product name"""
        # Extract order ID
        order_match = re.search(r'(ord\d+)', response, re.IGNORECASE)
        if not order_match:
            return self._quick_format(response)
            
        order_id = order_match.group(1).upper()
        
        # Extract product name (look for common patterns)
        product = "Unknown"
        
        # Pattern 1: Product (OrderID) - Status
        product_match = re.search(r'([a-zA-Z\s]+)\s*\(\s*' + re.escape(order_id) + r'\s*\)', response, re.IGNORECASE)
        if product_match:
            product = product_match.group(1).strip()
        else:
            # Pattern 2: Look for product before order ID
            parts = response.split(order_id)
            if len(parts) > 1:
                before_order = parts[0].strip()
                # Take last 1-2 words before order ID
                words = before_order.split()
                if len(words) >= 1:
                    # Take the last 1-2 words as product name
                    product_words = words[-2:] if len(words) >= 2 else [words[-1]]
                    # Filter out status words
                    product_words = [w for w in product_words if w.lower() not in ['total', 'order:', 'order', 'status:']]
                    if product_words:
                        product = ' '.join(product_words).title()
        
        # Extract status
        status = "Unknown"
        if "delivered" in response.lower():
            status = "Delivered ✅"
        elif "pending" in response.lower():
            status = "Pending ⏳"
        elif "returned" in response.lower():
            status = "Returned ↩️"
        elif "shipped" in response.lower():
            status = "Shipped 🚚"
        elif "cancelled" in response.lower():
            status = "Cancelled ❌"
        
        # Format: OrderID: Product - Status
        if product and product != "Unknown" and product != order_id and product != "Status":
            return f"• {order_id}: {product} - {status}"
        else:
            return f"• {order_id} - {status}"
    
    def _format_confirmation(self, response):
        """Format confirmation messages"""
        if "yes" in response.lower() and "no" in response.lower():
            return "• Yes - Confirm\n• No - Cancel"
        return response
    
    def _format_order_creation(self, response):
        """Format order creation responses"""
        # Extract order ID if present
        order_match = re.search(r'(ord\d+)', response, re.IGNORECASE)
        if order_match:
            order_id = order_match.group(1).upper()
            return f"• Order {order_id} created successfully ✅"
        
        # Extract product name if present
        product_patterns = [
            r'for\s+([a-zA-Z\s]+)',
            r'([a-zA-Z\s]+)\s+order',
            r'created.*?([a-zA-Z\s]+)',
        ]
        
        for pattern in product_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                product = match.group(1).strip().title()
                return f"• {product} order created ✅"
        
        return "• Order created successfully ✅"
    
    def _format_clarification(self, response):
        """Format clarification requests"""
        lines = response.split('\n')
        short_lines = []
        for line in lines:
            if line.strip():
                short_lines.append(f"• {line.strip()}")
        return '\n'.join(short_lines)
    
    def _format_general(self, user_question, bot_response):
        """Format general responses with Gemini"""
        try:
            prompt = f"""
            Make this response SHORT and DIRECT:
            
            Q: {user_question}
            A: {bot_response}
            
            Rules:
            - Line-by-line format
            - No paragraphs
            - Only essential info
            - Use bullet points
            - Max 2-3 lines
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return self._quick_format(bot_response)
    
    def _quick_format(self, response):
        """Quick formatting without Gemini"""
        # Split into lines and clean up
        lines = response.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('You have') and not line.startswith('Your'):
                # Convert to bullet point if not already
                if not line.startswith('•'):
                    line = f"• {line}"
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines[:5])  # Max 5 lines
    
    def is_available(self):
        return self.model is not None
