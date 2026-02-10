'use client'

/**
 * T050: TaskFilters component for filtering tasks.
 *
 * Phase V: New component for filtering by:
 * - Priority (LOW, MEDIUM, HIGH)
 * - Tags
 * - Due date range (before/after)
 * - Search query
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { colors, borderRadius, spacing } from '@/styles/tokens'
import { fadeIn } from '@/lib/animations'

export interface TaskFilters {
  priority?: 'LOW' | 'MEDIUM' | 'HIGH'
  tags?: string[]
  dueBefore?: string
  dueAfter?: string
  search?: string
  sortBy?: 'created_at' | 'updated_at' | 'due_date' | 'priority'
  sortOrder?: 'asc' | 'desc'
}

interface TaskFiltersProps {
  filters: TaskFilters
  onFiltersChange: (filters: TaskFilters) => void
  availableTags?: string[]
}

export default function TaskFilters({ filters, onFiltersChange, availableTags = [] }: TaskFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const handlePriorityChange = (priority: 'LOW' | 'MEDIUM' | 'HIGH' | undefined) => {
    onFiltersChange({ ...filters, priority })
  }

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || []
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag]
    onFiltersChange({ ...filters, tags: newTags })
  }

  const handleSearchChange = (search: string) => {
    onFiltersChange({ ...filters, search })
  }

  const handleSortChange = (sortBy: TaskFilters['sortBy'], sortOrder: TaskFilters['sortOrder']) => {
    onFiltersChange({ ...filters, sortBy, sortOrder })
  }

  const clearAllFilters = () => {
    onFiltersChange({})
  }

  const hasActiveFilters = !!(
    filters.priority ||
    (filters.tags && filters.tags.length > 0) ||
    filters.dueBefore ||
    filters.dueAfter ||
    filters.search
  )

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="bg-white rounded-xl shadow-sm"
      style={{
        border: `2px solid ${colors.neutral[200]}`,
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ borderBottom: isExpanded ? `1px solid ${colors.neutral[200]}` : 'none' }}
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: colors.primary[600] }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <h3 className="font-semibold" style={{ color: colors.neutral[800] }}>Filter Tasks</h3>
          {hasActiveFilters && (
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold" style={{
              backgroundColor: colors.primary[100],
              color: colors.primary[700]
            }}>
              Active
            </span>
          )}
        </div>
        <motion.svg
          className="w-5 h-5 transition-transform"
          style={{ color: colors.neutral[500] }}
          animate={{ rotate: isExpanded ? 180 : 0 }}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="p-5 space-y-5">
              {/* Search */}
              <div>
                <label className="block text-sm font-semibold mb-2" style={{ color: colors.neutral[700] }}>
                  Search
                </label>
                <input
                  type="text"
                  placeholder="Search tasks..."
                  value={filters.search || ''}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border-2 focus:outline-none focus:ring-2"
                  style={{
                    borderColor: colors.neutral[300],
                    color: colors.neutral[900],
                  }}
                />
              </div>

              {/* Priority Filter */}
              <div>
                <label className="block text-sm font-semibold mb-2" style={{ color: colors.neutral[700] }}>
                  Priority
                </label>
                <div className="flex flex-wrap gap-2">
                  {(['LOW', 'MEDIUM', 'HIGH'] as const).map((priority) => (
                    <button
                      key={priority}
                      onClick={() => handlePriorityChange(filters.priority === priority ? undefined : priority)}
                      className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                      style={{
                        backgroundColor: filters.priority === priority
                          ? priority === 'HIGH' ? colors.error[500]
                          : priority === 'MEDIUM' ? colors.warning[500]
                          : colors.success[500]
                          : colors.neutral[100],
                        color: filters.priority === priority ? colors.white : colors.neutral[700],
                        border: `2px solid ${filters.priority === priority
                          ? 'transparent'
                          : colors.neutral[300]}`,
                      }}
                    >
                      {priority}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags Filter */}
              {availableTags.length > 0 && (
                <div>
                  <label className="block text-sm font-semibold mb-2" style={{ color: colors.neutral[700] }}>
                    Tags
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {availableTags.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => handleTagToggle(tag)}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                        style={{
                          backgroundColor: (filters.tags || []).includes(tag)
                            ? colors.primary[500]
                            : colors.neutral[100],
                          color: (filters.tags || []).includes(tag)
                            ? colors.white
                            : colors.neutral[700],
                          border: `2px solid ${(filters.tags || []).includes(tag)
                            ? colors.primary[500]
                            : colors.neutral[300]}`,
                        }}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Sort */}
              <div>
                <label className="block text-sm font-semibold mb-2" style={{ color: colors.neutral[700] }}>
                  Sort By
                </label>
                <div className="flex gap-2">
                  <select
                    value={filters.sortBy || 'created_at'}
                    onChange={(e) => handleSortChange(
                      e.target.value as TaskFilters['sortBy'],
                      filters.sortOrder || 'desc'
                    )}
                    className="px-4 py-2.5 rounded-lg border-2 focus:outline-none flex-1"
                    style={{
                      borderColor: colors.neutral[300],
                      color: colors.neutral[900],
                    }}
                  >
                    <option value="created_at">Created</option>
                    <option value="updated_at">Updated</option>
                    <option value="due_date">Due Date</option>
                    <option value="priority">Priority</option>
                  </select>
                  <button
                    onClick={() => handleSortChange(
                      filters.sortBy || 'created_at',
                      filters.sortOrder === 'asc' ? 'desc' : 'asc'
                    )}
                    className="px-4 py-2.5 rounded-lg border-2 font-medium transition-all"
                    style={{
                      borderColor: colors.neutral[300],
                      backgroundColor: colors.white,
                      color: colors.neutral[700],
                    }}
                  >
                    {filters.sortOrder === 'asc' ? '↑' : '↓'}
                  </button>
                </div>
              </div>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="w-full px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: colors.error[50],
                    color: colors.error[700],
                    border: `2px solid ${colors.error[200]}`,
                  }}
                >
                  Clear All Filters
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
