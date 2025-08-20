#!/usr/bin/env python3
"""
Fix competitive advantages chart - move Customer Service label instead of score.
"""

import matplotlib.pyplot as plt
import numpy as np

# Set up professional styling
plt.style.use('default')

# Create custom color schemes
colors = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'accent': '#F18F01',
    'success': '#C73E1D',
    'neutral': '#6C757D',
    'light': '#F8F9FA',
    'dark': '#343A40'
}

def create_fixed_competitive_advantages():
    """Create competitive advantages visualization with fixes."""
    fig = plt.figure(figsize=(18, 14))
    
    # Add main title with lots of space
    fig.suptitle('Competitive Advantages Analysis\nBased on Guest Feedback', 
                 fontsize=24, fontweight='bold', y=0.95)
    
    # Create subplot with generous spacing
    ax = fig.add_subplot(111, projection='polar')
    ax.set_position([0.1, 0.15, 0.8, 0.7])  # Leave lots of space for title
    
    # Create radar chart for competitive advantages
    categories = ['Customer Service', 'Cleanliness', 'Location', 'Amenities', 'Communication', 'Value']
    
    # Scores based on our analysis (0-10 scale)
    scores = [9.5, 8.0, 7.5, 7.0, 8.5, 7.8]  # Relative importance scores
    
    # Number of variables
    N = len(categories)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    # Add the first value to the end to close the plot
    scores += scores[:1]
    
    # Create the plot
    ax.plot(angles, scores, 'o-', linewidth=3, color=colors['primary'], markersize=10)
    ax.fill(angles, scores, alpha=0.25, color=colors['primary'])
    
    # Set the labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=16, fontweight='bold')
    
    # Set the y-axis limits
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=14)
    
    # Remove the y-axis label (Competitive Advantage Score)
    ax.set_ylabel('')  # This removes the axis label
    
    # Add score annotations with normal positioning
    for i, (angle, score) in enumerate(zip(angles[:-1], scores[:-1])):
        ax.text(angle, score + 1.0, f'{score:.1f}', 
                ha='center', va='center', fontweight='bold', fontsize=15,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor='gray'))
    
    # Now manually reposition the Customer Service label to avoid overlap
    # Get the Customer Service angle (first category)
    customer_service_angle = angles[0]
    
    # Remove the original Customer Service label
    ax.set_xticklabels(['', 'Cleanliness', 'Location', 'Amenities', 'Communication', 'Value'], fontsize=16, fontweight='bold')
    
    # Add Customer Service label closer to the blue data point - NO RECTANGLE
    ax.text(customer_service_angle, 6.5, 'Customer Service', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    plt.savefig('reports/08_competitive_advantages.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created fixed competitive advantages chart - Customer Service label closer to blue point")

if __name__ == "__main__":
    create_fixed_competitive_advantages() 