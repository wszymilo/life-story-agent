import { useNavigate } from 'react-router-dom'
import { EventData } from '../services/events'

interface EventCardProps {
  event: EventData
  onClick?: (event: EventData) => void
}

export function EventCard({ event, onClick }: EventCardProps) {
  const navigate = useNavigate()
  const isDraft = event.status === 'draft'

  const handleClick = () => {
    if (onClick) {
      onClick(event)
    } else {
      navigate(`/event/${event.id}`)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown date'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  const displayDate = event.time_anchor_date || event.time_anchor || event.created_at
  const summaryPreview = event.summary
    ? event.summary.slice(0, 100) + (event.summary.length > 100 ? '...' : '')
    : null

  return (
    <button
      onClick={handleClick}
      className="w-full text-left bg-white rounded-xl shadow-sm p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900 flex-1">
          {event.title || 'Untitled Memory'}
        </h3>
        {isDraft && (
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full ml-2">
            Draft
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-2">{formatDate(displayDate)}</p>

      {event.place && (
        <p className="text-sm text-gray-500 mb-2">{event.place}</p>
      )}

      {summaryPreview && (
        <p className="text-sm text-gray-700 line-clamp-2">{summaryPreview}</p>
      )}

      {isDraft && (
        <p className="text-sm text-blue-600 mt-2 font-medium">Tap to continue →</p>
      )}
    </button>
  )
}