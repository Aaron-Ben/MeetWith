"""
TavilySearch Plugin
"""

import sys
import json
import os


def main():
    """Main function to handle plugin execution"""

    # Read input from stdin
    try:
        input_data = sys.stdin.read()
    except Exception as e:
        output = {"status": "error", "error": f"Failed to read stdin: {str(e)}"}
        print(json.dumps(output))
        sys.exit(1)

    output = {}

    try:
        if not input_data.strip():
            raise ValueError("No input data received from stdin.")

        data = json.loads(input_data)

        # Extract parameters with defaults
        query = data.get('query')
        topic = data.get('topic', 'general')
        search_depth = data.get('search_depth', 'basic')
        max_results = data.get('max_results', 5)

        if not query:
            raise ValueError("Missing required argument: query")

        # Validate search_depth
        valid_depths = ['basic', 'advanced']
        if search_depth not in valid_depths:
            search_depth = 'basic'

        # Validate max_results
        try:
            max_results = int(max_results)
            if max_results < 5 or max_results > 100:
                max_results = 5
        except (ValueError, TypeError):
            max_results = 5

        # Get API key from environment
        api_key = os.environ.get('TAVILY_API_KEY')
        if not api_key:
            # Also try alternate key name for compatibility
            api_key = os.environ.get('TavilyKey')

        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set in config.env.")

        # Import tavily-python and perform search
        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError("tavily-python package not installed. Install with: pip install tavily-python")

        # Initialize Tavily client
        client = TavilyClient(api_key=api_key)

        # Perform search
        response = client.search(
            query=query,
            search_depth=search_depth,
            topic=topic,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
            include_images=False
        )

        output = {"status": "success", "result": response}

    except json.JSONDecodeError as e:
        output = {"status": "error", "error": f"Invalid JSON input: {str(e)}"}
    except ValueError as e:
        output = {"status": "error", "error": f"Validation Error: {str(e)}"}
    except ImportError as e:
        output = {"status": "error", "error": f"Import Error: {str(e)}"}
    except Exception as e:
        output = {"status": "error", "error": f"Tavily Search Error: {str(e)}"}

    # Output JSON to stdout
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
