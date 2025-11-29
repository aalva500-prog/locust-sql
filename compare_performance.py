#!/usr/bin/env python3
"""
Performance Comparison Script for Calcite vs Non-Calcite
Compares performance test results and generates a detailed comparison CSV
"""

import csv
import sys
from pathlib import Path


def read_csv_data(filepath):
    """Read CSV file and return data as list of dictionaries"""
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def calculate_percentage_change(calcite_val, non_calcite_val):
    """Calculate percentage change from non-calcite to calcite"""
    try:
        calcite_float = float(calcite_val)
        non_calcite_float = float(non_calcite_val)
        
        if non_calcite_float == 0:
            return "N/A"
        
        change = ((calcite_float - non_calcite_float) / non_calcite_float) * 100
        return f"{change:.2f}%"
    except (ValueError, ZeroDivisionError):
        return "N/A"


def get_file_input(prompt, default=None):
    """Prompt user for file path input"""
    if default:
        prompt = f"{prompt}\n  (Press Enter for default: {default})\n  Path: "
    else:
        prompt = f"{prompt}\n  Path: "
    
    while True:
        user_input = input(prompt).strip()
        
        # Use default if provided and user pressed Enter
        if not user_input and default:
            return Path(default)
        
        if not user_input:
            print("  ⚠️  Please provide a file path.")
            continue
        
        filepath = Path(user_input)
        
        # Check if file exists (for input files)
        if "output" not in prompt.lower():
            if not filepath.exists():
                print(f"  ❌ Error: File not found: {filepath}")
                retry = input("  Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return None
                continue
        
        return filepath


def determine_ppl_directory(calcite_file):
    """Determine the PPL directory based on the input file name"""
    filename = calcite_file.name.lower()
    
    # Check for common patterns in filename
    if 'vpc' in filename:
        return 'vpc'
    elif 'nfw' in filename or 'networkfirewall' in filename:
        return 'nfw'
    elif 'cloudtrail' in filename:
        return 'cloudtrail'
    elif 'waf' in filename:
        return 'waf'
    elif 'big5' in filename:
        return 'big5'
    
    # Try parent directory name
    parent_name = calcite_file.parent.name.lower()
    if parent_name in ['vpc', 'nfw', 'cloudtrail', 'waf', 'big5']:
        return parent_name
    
    return None


def read_ppl_query(query_name, ppl_base_dir):
    """Read PPL query content from file"""
    if not ppl_base_dir:
        return "N/A"
    
    # Extract the actual filename from the query name
    # Query names can be like "PPL Query: vpc/01_count_all" or just "01_count_all"
    if "PPL Query:" in query_name:
        # Extract the part after the colon and remove any path prefix
        parts = query_name.split(":", 1)
        if len(parts) > 1:
            query_name = parts[1].strip()
    
    # Remove any directory prefix (e.g., "vpc/" or "nfw/")
    if "/" in query_name:
        query_name = query_name.split("/")[-1]
    
    # Try to find the .ppl file
    ppl_file = ppl_base_dir / f"{query_name}.ppl"
    
    if ppl_file.exists():
        try:
            with open(ppl_file, 'r') as f:
                return f.read().strip()
        except Exception:
            return "N/A"
    
    return "N/A"


def compare_performance(calcite_file, non_calcite_file, output_file, ppl_type=None):
    """Compare performance between calcite and non-calcite results"""
    
    print(f"\nReading calcite results from: {calcite_file}")
    calcite_data = read_csv_data(calcite_file)
    
    print(f"Reading non-calcite results from: {non_calcite_file}")
    non_calcite_data = read_csv_data(non_calcite_file)
    
    # Find PPL directory if log type was provided
    ppl_base_dir = None
    
    if ppl_type:
        # Try to find ppl directory relative to the script or input file
        script_dir = Path(__file__).parent
        possible_dirs = [
            script_dir / 'ppl' / ppl_type,
            calcite_file.parent.parent / 'ppl' / ppl_type,
            Path.cwd() / 'ppl' / ppl_type,
        ]
        
        for dir_path in possible_dirs:
            if dir_path.exists() and dir_path.is_dir():
                ppl_base_dir = dir_path
                print(f"Found PPL queries in: {ppl_base_dir}")
                break
        
        if not ppl_base_dir:
            print(f"⚠️  Warning: Could not find PPL query directory for '{ppl_type}'. Query column will show 'N/A'")
    else:
        print("⚠️  No log type specified. Query column will show 'N/A'")
    
    # Create a mapping of query names to data
    calcite_map = {row['Name']: row for row in calcite_data}
    non_calcite_map = {row['Name']: row for row in non_calcite_data}
    
    # Prepare comparison results
    comparison_results = []
    
    # Get all unique query names
    all_queries = sorted(set(list(calcite_map.keys()) + list(non_calcite_map.keys())))
    
    for query_name in all_queries:
        calcite_row = calcite_map.get(query_name, {})
        non_calcite_row = non_calcite_map.get(query_name, {})
        
        if not calcite_row or not non_calcite_row:
            continue
        
        # Determine which performs better based on average response time
        calcite_avg = float(calcite_row.get('Average Response Time', '0'))
        non_calcite_avg = float(non_calcite_row.get('Average Response Time', '0'))
        
        if calcite_avg < non_calcite_avg:
            better_performance = "Calcite"
            performance_improvement = f"{((non_calcite_avg - calcite_avg) / non_calcite_avg * 100):.2f}% faster"
        elif non_calcite_avg < calcite_avg:
            better_performance = "Non-Calcite"
            performance_improvement = f"{((calcite_avg - non_calcite_avg) / calcite_avg * 100):.2f}% faster"
        else:
            better_performance = "Equal"
            performance_improvement = "Same performance"
        
        # Read PPL query if available
        ppl_query = read_ppl_query(query_name, ppl_base_dir) if query_name != 'Aggregated' else 'N/A'
        
        comparison = {
            'Query Name': query_name,
            'PPL Query': ppl_query,
            'Better Performance': better_performance,
            'Performance Improvement': performance_improvement,
            
            # Request counts
            'Calcite Request Count': calcite_row.get('Request Count', 'N/A'),
            'Non-Calcite Request Count': non_calcite_row.get('Request Count', 'N/A'),
            
            # Median response time
            'Calcite Median (ms)': calcite_row.get('Median Response Time', 'N/A'),
            'Non-Calcite Median (ms)': non_calcite_row.get('Median Response Time', 'N/A'),
            'Median Change': calculate_percentage_change(
                calcite_row.get('Median Response Time', '0'),
                non_calcite_row.get('Median Response Time', '0')
            ),
            
            # Average response time
            'Calcite Average (ms)': calcite_row.get('Average Response Time', 'N/A'),
            'Non-Calcite Average (ms)': non_calcite_row.get('Average Response Time', 'N/A'),
            'Average Change': calculate_percentage_change(
                calcite_row.get('Average Response Time', '0'),
                non_calcite_row.get('Average Response Time', '0')
            ),
            
            # Min response time
            'Calcite Min (ms)': calcite_row.get('Min Response Time', 'N/A'),
            'Non-Calcite Min (ms)': non_calcite_row.get('Min Response Time', 'N/A'),
            'Min Change': calculate_percentage_change(
                calcite_row.get('Min Response Time', '0'),
                non_calcite_row.get('Min Response Time', '0')
            ),
            
            # Max response time
            'Calcite Max (ms)': calcite_row.get('Max Response Time', 'N/A'),
            'Non-Calcite Max (ms)': non_calcite_row.get('Max Response Time', 'N/A'),
            'Max Change': calculate_percentage_change(
                calcite_row.get('Max Response Time', '0'),
                non_calcite_row.get('Max Response Time', '0')
            ),
            
            # 95th percentile
            'Calcite 95% (ms)': calcite_row.get('95%', 'N/A'),
            'Non-Calcite 95% (ms)': non_calcite_row.get('95%', 'N/A'),
            '95% Change': calculate_percentage_change(
                calcite_row.get('95%', '0'),
                non_calcite_row.get('95%', '0')
            ),
            
            # 99th percentile
            'Calcite 99% (ms)': calcite_row.get('99%', 'N/A'),
            'Non-Calcite 99% (ms)': non_calcite_row.get('99%', 'N/A'),
            '99% Change': calculate_percentage_change(
                calcite_row.get('99%', '0'),
                non_calcite_row.get('99%', '0')
            ),
            
            # Requests per second
            'Calcite Requests/s': calcite_row.get('Requests/s', 'N/A'),
            'Non-Calcite Requests/s': non_calcite_row.get('Requests/s', 'N/A'),
            'Requests/s Change': calculate_percentage_change(
                calcite_row.get('Requests/s', '0'),
                non_calcite_row.get('Requests/s', '0')
            ),
            
            # Failure counts
            'Calcite Failures': calcite_row.get('Failure Count', 'N/A'),
            'Non-Calcite Failures': non_calcite_row.get('Failure Count', 'N/A'),
        }
        
        comparison_results.append(comparison)
    
    # Write comparison results to CSV
    if comparison_results:
        fieldnames = comparison_results[0].keys()
        
        print(f"\nWriting comparison results to: {output_file}")
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comparison_results)
        
        print(f"\n✅ Successfully created comparison file: {output_file}")
        print(f"   Total queries compared: {len(comparison_results)}")
        
        # Print summary statistics
        print("\n" + "="*80)
        print("SUMMARY STATISTICS")
        print("="*80)
        
        # Find aggregated rows for summary
        aggregated_calcite = calcite_map.get('Aggregated', {})
        aggregated_non_calcite = non_calcite_map.get('Aggregated', {})
        
        if aggregated_calcite and aggregated_non_calcite:
            print("\nAggregated Results:")
            print(f"  Calcite Average Response Time:     {aggregated_calcite.get('Average Response Time', 'N/A')} ms")
            print(f"  Non-Calcite Average Response Time: {aggregated_non_calcite.get('Average Response Time', 'N/A')} ms")
            avg_change = calculate_percentage_change(
                aggregated_calcite.get('Average Response Time', '0'),
                aggregated_non_calcite.get('Average Response Time', '0')
            )
            print(f"  Change: {avg_change}")
            
            print(f"\n  Calcite Median Response Time:      {aggregated_calcite.get('Median Response Time', 'N/A')} ms")
            print(f"  Non-Calcite Median Response Time:  {aggregated_non_calcite.get('Median Response Time', 'N/A')} ms")
            median_change = calculate_percentage_change(
                aggregated_calcite.get('Median Response Time', '0'),
                aggregated_non_calcite.get('Median Response Time', '0')
            )
            print(f"  Change: {median_change}")
            
            print(f"\n  Calcite Total Requests:     {aggregated_calcite.get('Request Count', 'N/A')}")
            print(f"  Non-Calcite Total Requests: {aggregated_non_calcite.get('Request Count', 'N/A')}")
            
            print(f"\n  Calcite Requests/s:     {aggregated_calcite.get('Requests/s', 'N/A')}")
            print(f"  Non-Calcite Requests/s: {aggregated_non_calcite.get('Requests/s', 'N/A')}")
            rps_change = calculate_percentage_change(
                aggregated_calcite.get('Requests/s', '0'),
                non_calcite_row.get('Requests/s', '0')
            )
            print(f"  Change: {rps_change}")
            
            # Count winners
            calcite_wins = sum(1 for r in comparison_results if r['Better Performance'] == 'Calcite' and r['Query Name'] != 'Aggregated')
            non_calcite_wins = sum(1 for r in comparison_results if r['Better Performance'] == 'Non-Calcite' and r['Query Name'] != 'Aggregated')
            
            print(f"\n  Query Performance Summary:")
            print(f"    Calcite wins:     {calcite_wins} queries")
            print(f"    Non-Calcite wins: {non_calcite_wins} queries")
        
        print("\n" + "="*80)
    else:
        print("⚠️  No matching queries found to compare")
        return 1
    
    return 0


def main():
    """Main function"""
    print("="*80)
    print("CALCITE VS NON-CALCITE PERFORMANCE COMPARISON")
    print("="*80)
    print()
    
    # Check if command line arguments are provided
    if len(sys.argv) >= 3:
        # Use command line arguments
        calcite_file = Path(sys.argv[1])
        non_calcite_file = Path(sys.argv[2])
        output_file = Path(sys.argv[3]) if len(sys.argv) >= 4 else Path("calcite_vs_non_calcite_comparison.csv")
        
        # Verify files exist
        if not calcite_file.exists():
            print(f"❌ Error: Calcite file not found: {calcite_file}")
            return 1
        
        if not non_calcite_file.exists():
            print(f"❌ Error: Non-Calcite file not found: {non_calcite_file}")
            return 1
    else:
        # Interactive mode - prompt user for inputs
        print("📋 Interactive Mode")
        print("-" * 80)
        print("\nPlease provide the file paths for the comparison.\n")
        
        # Get calcite file
        calcite_file = get_file_input(
            "Enter the path to the CALCITE performance results CSV:"
        )
        if not calcite_file:
            print("\n❌ Aborted.")
            return 1
        
        # Get non-calcite file
        non_calcite_file = get_file_input(
            "\nEnter the path to the NON-CALCITE performance results CSV:"
        )
        if not non_calcite_file:
            print("\n❌ Aborted.")
            return 1
        
        # Ask for log type to find PPL queries
        print("\n" + "-" * 80)
        print("Log Type Selection (for PPL query inclusion)")
        print("-" * 80)
        print("\nAvailable log types:")
        print("  1. vpc        - VPC Flow Logs")
        print("  2. nfw        - Network Firewall Logs")
        print("  3. cloudtrail - CloudTrail Logs")
        print("  4. waf        - WAF Logs")
        print("  5. big5       - Big5 Logs")
        print("  6. skip       - Skip PPL query inclusion\n")
        
        log_type = None
        while True:
            user_input = input("Enter log type (vpc/nfw/cloudtrail/waf/big5/skip): ").strip().lower()
            
            if user_input in ['vpc', 'nfw', 'cloudtrail', 'waf', 'big5']:
                log_type = user_input
                break
            elif user_input == 'skip':
                log_type = None
                break
            else:
                print("  ⚠️  Invalid log type. Please enter vpc, nfw, cloudtrail, waf, big5, or skip.")
        
        # Automatically generate output filename in the same directory as calcite file
        output_dir = calcite_file.parent
        output_file = output_dir / "calcite_vs_non_calcite_comparison.csv"
        
        print(f"\n📝 Output will be saved to: {output_file}")
        print("\n" + "="*80)
    
    return compare_performance(calcite_file, non_calcite_file, output_file, ppl_type=log_type)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
