'use client';

import { useState, useEffect } from 'react';
import { Check, Plus, X } from 'lucide-react';

interface Interest {
  category: string;
  selected: boolean;
}

const AVAILABLE_CATEGORIES = [
  'Technology',
  'Business',
  'Sports',
  'Entertainment',
  'Health',
  'Science',
  'Politics',
  'World',
  'Finance',
  'Education',
  'Environment',
  'Food',
  'Travel',
  'Fashion',
  'Gaming',
  'Automotive',
  'Real Estate',
  'Lifestyle'
];

interface InterestManagerProps {
  userInterests: string[];
  onUpdate: (interests: string[]) => void;
  compact?: boolean;
}

export default function InterestManager({ userInterests, onUpdate, compact = false }: InterestManagerProps) {
  const [interests, setInterests] = useState<Interest[]>([]);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    const interestList = AVAILABLE_CATEGORIES.map(category => ({
      category,
      selected: userInterests.includes(category)
    }));
    setInterests(interestList);
  }, [userInterests]);

  const toggleInterest = (category: string) => {
    const updated = interests.map(interest =>
      interest.category === category
        ? { ...interest, selected: !interest.selected }
        : interest
    );
    setInterests(updated);
  };

  const saveInterests = () => {
    const selectedInterests = interests
      .filter(interest => interest.selected)
      .map(interest => interest.category);
    onUpdate(selectedInterests);
    setIsEditing(false);
  };

  const cancelEditing = () => {
    // Reset to original
    const interestList = AVAILABLE_CATEGORIES.map(category => ({
      category,
      selected: userInterests.includes(category)
    }));
    setInterests(interestList);
    setIsEditing(false);
  };

  const selectedCount = interests.filter(i => i.selected).length;

  if (compact && !isEditing) {
    return (
      <div className="flex flex-wrap gap-2">
        {interests
          .filter(i => i.selected)
          .map(interest => (
            <span
              key={interest.category}
              className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium"
            >
              {interest.category}
            </span>
          ))}
        <button
          onClick={() => setIsEditing(true)}
          className="px-3 py-1 border-2 border-dashed border-border hover:border-primary text-text-secondary hover:text-primary rounded-full text-sm font-medium transition-colors flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          Edit Interests
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {isEditing && (
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-text">Choose Your Interests</h3>
            <p className="text-sm text-text-secondary">
              {selectedCount} {selectedCount === 1 ? 'topic' : 'topics'} selected • This helps personalize your feed
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={cancelEditing}
              className="px-4 py-2 text-text-secondary hover:bg-hover rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={saveInterests}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {interests.map(interest => (
          <button
            key={interest.category}
            onClick={() => isEditing && toggleInterest(interest.category)}
            disabled={!isEditing}
            className={`
              px-4 py-3 rounded-lg font-medium text-sm transition-all duration-200
              ${interest.selected
                ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-md'
                : 'bg-surface border-2 border-border text-text-secondary hover:border-primary'
              }
              ${isEditing ? 'cursor-pointer hover:scale-105' : 'cursor-default'}
              ${!isEditing && interest.selected ? 'ring-2 ring-primary/20' : ''}
            `}
          >
            {interest.selected && (
              <Check className="w-4 h-4 inline mr-1" />
            )}
            {interest.category}
          </button>
        ))}
      </div>

      {!isEditing && !compact && (
        <button
          onClick={() => setIsEditing(true)}
          className="w-full px-4 py-3 border-2 border-dashed border-border hover:border-primary text-text-secondary hover:text-primary rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Edit Your Interests
        </button>
      )}
    </div>
  );
}
