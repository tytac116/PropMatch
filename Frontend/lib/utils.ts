import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Function to get the color for a search score
export function getScoreColor(score: number) {
  if (score >= 95) return 'bg-emerald-500 text-white';      // 95-100%: Bright green
  if (score >= 85) return 'bg-green-500 text-white';        // 85-94%: Green  
  if (score >= 75) return 'bg-lime-500 text-white';         // 75-84%: Lime green
  if (score >= 65) return 'bg-yellow-500 text-white';       // 65-74%: Yellow
  if (score >= 55) return 'bg-amber-500 text-white';        // 55-64%: Amber
  if (score >= 45) return 'bg-orange-500 text-white';       // 45-54%: Orange
  if (score >= 35) return 'bg-red-500 text-white';          // 35-44%: Red
  return 'bg-red-600 text-white';                           // Below 35%: Dark red
}

// Format currency with comma separators
export function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat('en-ZA', { 
    style: 'currency', 
    currency: currency,
    maximumFractionDigits: 0
  }).format(amount);
}

// Format date to readable format
export function formatDate(dateString: string) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-ZA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(date);
}

// Create truncated text with ellipsis if it exceeds max length
export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}