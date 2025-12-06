#!/usr/bin/env python3
"""
Performance Visualization Script for Calcite vs Non-Calcite Comparison

This script generates multiple visualizations to compare performance metrics
between Calcite and Non-Calcite query execution.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

def load_data(csv_path):
    """Load and prepare the CSV data"""
    df = pd.read_csv(csv_path)
    # Remove the aggregated row for individual query analysis
    df_queries = df[df['Query Name'] != 'Aggregated'].copy()
    df_aggregated = df[df['Query Name'] == 'Aggregated'].copy()
    return df_queries, df_aggregated

def create_median_comparison(df, output_dir):
    """Create bar chart comparing median response times"""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    queries = df['Query Name'].str.replace('PPL Query: cloudtrail/', '', regex=False)
    x = np.arange(len(queries))
    width = 0.35
    
    calcite_median = df['Calcite Median (ms)']
    non_calcite_median = df['Non-Calcite Median (ms)']
    
    bars1 = ax.bar(x - width/2, calcite_median, width, label='Calcite', 
                   color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, non_calcite_median, width, label='Non-Calcite', 
                   color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Query', fontweight='bold', fontsize=12)
    ax.set_ylabel('Median Response Time (ms)', fontweight='bold', fontsize=12)
    ax.set_title('Median Response Time Comparison: Calcite vs Non-Calcite\n(Lower is Better)', 
                 fontweight='bold', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45, ha='right')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'median_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: median_comparison.png")
    plt.close()

def create_performance_improvement(df, output_dir):
    """Create bar chart showing performance improvement percentage"""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    queries = df['Query Name'].str.replace('PPL Query: cloudtrail/', '', regex=False)
    x = np.arange(len(queries))
    
    # Extract percentage values and determine winner
    improvements = []
    colors = []
    for _, row in df.iterrows():
        perf_str = row['Performance Improvement']
        # Extract the percentage number
        perf_value = float(perf_str.split('%')[0])
        
        # If Calcite is better, make it negative for visual distinction
        if row['Better Performance'] == 'Calcite':
            improvements.append(-perf_value)
            colors.append('#2E86AB')
        else:
            improvements.append(perf_value)
            colors.append('#A23B72')
    
    bars = ax.bar(x, improvements, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, improvements)):
        height = bar.get_height()
        label = f'{abs(val):.1f}%'
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='top', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Query', fontweight='bold', fontsize=12)
    ax.set_ylabel('Performance Improvement (%)', fontweight='bold', fontsize=12)
    ax.set_title('Performance Improvement by Query\n(Non-Calcite Positive / Calcite Negative)', 
                 fontweight='bold', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45, ha='right')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.grid(axis='y', alpha=0.3)
    
    # Custom legend
    calcite_patch = mpatches.Patch(color='#2E86AB', label='Calcite Faster', alpha=0.8)
    non_calcite_patch = mpatches.Patch(color='#A23B72', label='Non-Calcite Faster', alpha=0.8)
    ax.legend(handles=[calcite_patch, non_calcite_patch], fontsize=12, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'performance_improvement.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: performance_improvement.png")
    plt.close()

def create_percentile_comparison(df, output_dir):
    """Create separate charts for 95th and 99th percentile comparisons"""
    queries = df['Query Name'].str.replace('PPL Query: cloudtrail/', '', regex=False)
    x = np.arange(len(queries))
    width = 0.35
    
    # 95th Percentile Chart
    fig, ax = plt.subplots(figsize=(16, 10))
    
    calcite_95 = df['Calcite 95% (ms)']
    non_calcite_95 = df['Non-Calcite 95% (ms)']
    
    bars1 = ax.bar(x - width/2, calcite_95, width, label='Calcite', 
                   color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, non_calcite_95, width, label='Non-Calcite', 
                   color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Query', fontweight='bold', fontsize=12)
    ax.set_ylabel('95th Percentile Response Time (ms)', fontweight='bold', fontsize=12)
    ax.set_title('95th Percentile Response Time Comparison\n(Lower is Better)', 
                 fontweight='bold', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45, ha='right')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'p95_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: p95_comparison.png")
    plt.close()
    
    # 99th Percentile Chart
    fig, ax = plt.subplots(figsize=(16, 10))
    
    calcite_99 = df['Calcite 99% (ms)']
    non_calcite_99 = df['Non-Calcite 99% (ms)']
    
    bars1 = ax.bar(x - width/2, calcite_99, width, label='Calcite', 
                   color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, non_calcite_99, width, label='Non-Calcite', 
                   color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Query', fontweight='bold', fontsize=12)
    ax.set_ylabel('99th Percentile Response Time (ms)', fontweight='bold', fontsize=12)
    ax.set_title('99th Percentile Response Time Comparison\n(Lower is Better)', 
                 fontweight='bold', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45, ha='right')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'p99_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: p99_comparison.png")
    plt.close()

def create_winner_summary(df, output_dir):
    """Create pie chart showing winner distribution"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Winner distribution
    winner_counts = df['Better Performance'].value_counts()
    colors_pie = ['#A23B72', '#2E86AB']
    # Adjust explode based on number of winners
    explode = tuple([0.05] * len(winner_counts))
    
    ax1.pie(winner_counts.values, labels=winner_counts.index, autopct='%1.1f%%',
            colors=colors_pie[:len(winner_counts)], explode=explode, shadow=True, startangle=90,
            textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax1.set_title('Which Performs Better?\n(Count of Queries)', 
                  fontweight='bold', fontsize=14, pad=20)
    
    # Average improvement by winner
    avg_improvements = []
    labels = []
    colors_bar = []
    
    for winner in ['Non-Calcite', 'Calcite']:
        winner_df = df[df['Better Performance'] == winner]
        if len(winner_df) > 0:
            # Extract average improvement percentage
            improvements = winner_df['Performance Improvement'].str.extract(r'(\d+\.?\d*)')[0].astype(float)
            avg_improvements.append(improvements.mean())
            labels.append(f'{winner}\n({len(winner_df)} queries)')
            colors_bar.append('#A23B72' if winner == 'Non-Calcite' else '#2E86AB')
    
    bars = ax2.bar(labels, avg_improvements, color=colors_bar, alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax2.set_ylabel('Average Performance Improvement (%)', fontweight='bold', fontsize=12)
    ax2.set_title('Average Performance Improvement\n(When Each is Faster)', 
                  fontweight='bold', fontsize=14, pad=20)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'winner_summary.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: winner_summary.png")
    plt.close()

def create_requests_per_second_comparison(df, output_dir):
    """Create comparison of requests per second"""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    queries = df['Query Name'].str.replace('PPL Query: cloudtrail/', '', regex=False)
    x = np.arange(len(queries))
    width = 0.35
    
    calcite_rps = df['Calcite Requests/s']
    non_calcite_rps = df['Non-Calcite Requests/s']
    
    bars1 = ax.bar(x - width/2, calcite_rps, width, label='Calcite', 
                   color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, non_calcite_rps, width, label='Non-Calcite', 
                   color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=8, rotation=0)
    
    ax.set_xlabel('Query', fontweight='bold', fontsize=12)
    ax.set_ylabel('Requests per Second', fontweight='bold', fontsize=12)
    ax.set_title('Throughput Comparison: Requests per Second\n(Higher is Better)', 
                 fontweight='bold', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45, ha='right')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'requests_per_second.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: requests_per_second.png")
    plt.close()

def create_aggregated_summary(df_agg, output_dir):
    """Create simplified summary visualization for aggregated data"""
    if len(df_agg) == 0:
        return
    
    row = df_agg.iloc[0]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('Overall Performance Summary (Aggregated Results)', 
                 fontweight='bold', fontsize=16, y=0.98)
    
    # 1. Response Time Metrics
    metrics = ['Median', '95%', '99%', 'Average', 'Max']
    calcite_times = [
        row['Calcite Median (ms)'],
        row['Calcite 95% (ms)'],
        row['Calcite 99% (ms)'],
        row['Calcite Average (ms)'],
        row['Calcite Max (ms)']
    ]
    non_calcite_times = [
        row['Non-Calcite Median (ms)'],
        row['Non-Calcite 95% (ms)'],
        row['Non-Calcite 99% (ms)'],
        row['Non-Calcite Average (ms)'],
        row['Non-Calcite Max (ms)']
    ]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, calcite_times, width, label='Calcite', 
                    color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, non_calcite_times, width, label='Non-Calcite', 
                    color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('Response Time (ms)', fontweight='bold', fontsize=13)
    ax1.set_title('Response Time Metrics Comparison', fontweight='bold', fontsize=14, pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontsize=11)
    ax1.legend(fontsize=12)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Performance Summary Text
    ax2.axis('off')
    winner = row['Better Performance']
    improvement = row['Performance Improvement']
    
    summary_text = f"""
    OVERALL WINNER: {winner}
    
    Performance Improvement: {improvement}
    
    Response Time Comparison:
    • Median: {row['Calcite Median (ms)']}ms vs {row['Non-Calcite Median (ms)']}ms
    • Average: {row['Calcite Average (ms)']:.1f}ms vs {row['Non-Calcite Average (ms)']:.1f}ms
    • 95th Percentile: {row['Calcite 95% (ms)']}ms vs {row['Non-Calcite 95% (ms)']}ms
    • 99th Percentile: {row['Calcite 99% (ms)']}ms vs {row['Non-Calcite 99% (ms)']}ms
    • Max: {row['Calcite Max (ms)']:.1f}ms vs {row['Non-Calcite Max (ms)']:.1f}ms
    
    Test Statistics:
    • Total Queries Tested: 16
    • Calcite Faster: 1 query (6.3%)
    • Non-Calcite Faster: 15 queries (93.8%)
    """
    
    ax2.text(0.05, 0.95, summary_text, transform=ax2.transAxes,
            fontsize=13, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5, pad=1))
    ax2.set_title('Performance Summary', fontweight='bold', fontsize=14, loc='left', pad=15)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'aggregated_summary.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: aggregated_summary.png")
    plt.close()

def create_all_visualizations(csv_path):
    """Generate all visualizations"""
    csv_path = Path(csv_path)
    output_dir = csv_path.parent / 'visualizations'
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n📊 Generating visualizations for: {csv_path.name}")
    print(f"📁 Output directory: {output_dir}\n")
    
    # Load data
    df_queries, df_aggregated = load_data(csv_path)
    
    print(f"Loaded {len(df_queries)} individual queries")
    print(f"Loaded {len(df_aggregated)} aggregated summary\n")
    
    # Generate all visualizations
    create_median_comparison(df_queries, output_dir)
    create_performance_improvement(df_queries, output_dir)
    create_percentile_comparison(df_queries, output_dir)
    create_winner_summary(df_queries, output_dir)
    create_aggregated_summary(df_aggregated, output_dir)
    
    print(f"\n✅ All visualizations saved to: {output_dir}")
    print(f"\nGenerated files:")
    for file in sorted(output_dir.glob('*.png')):
        print(f"  • {file.name}")

if __name__ == "__main__":
    import sys
    
    # Default path (relative to script location)
    default_csv = "performance_results/cloudtrail/calcite_vs_non_calcite_comparison_cloudtrail.csv"
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = default_csv
    
    create_all_visualizations(csv_path)
