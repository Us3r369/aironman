# TASKS_04: Performance Management Chart (PMC) UI Fixes and Improvements

## Session Goal
Fix and improve the Performance Management Chart section of the UI to ensure proper data display, functionality, and user experience.

## Priority Order and Technical Implementation

### 1. CRITICAL: Data Connection Investigation and Fix
**Issue**: Expected lines and datapoints are not displayed in the PMC chart.

**Technical Investigation Required**:
- [ ] Check browser console for JavaScript errors
- [ ] Verify API endpoints are returning data (check Network tab)
- [ ] Confirm chart library is receiving data correctly
- [ ] Validate data format matches chart library expectations
- [ ] Check if data transformation/preprocessing is working

**Implementation Steps**:
1. Add console logging to track data flow from API to chart
2. Verify `/api/pmc-metrics` endpoint returns expected data structure
3. Ensure chart component receives and processes data correctly
4. Test with sample data to isolate frontend vs backend issues

### 2. HIGH: Backend Data Freshness Verification
**Issue**: Need to verify backend fetches latest data and display timestamp.

**Technical Implementation**:
- [ ] Modify backend to include `last_updated` timestamp in PMC data response
- [ ] Add timestamp display in UI showing "Data last updated: [timestamp]"
- [ ] Ensure backend queries use most recent database records
- [ ] Add database query optimization for latest data retrieval

**API Response Structure Update**:
```json
{
  "ctl_data": [...],
  "atl_data": [...],
  "tsb_data": [...],
  "daily_tss_data": [...],
  "metadata": {
    "last_updated": "2025-01-10T15:30:00Z",
    "data_source": "database",
    "record_count": 42
  }
}
```

### 3. HIGH: Timeframe Selection Functionality
**Issue**: Timeframe buttons (7, 14, 30, 60, 90 days) not connected to data or chart updates.

**Technical Implementation**:
- [ ] Implement backend date filtering in PMC API endpoint
- [ ] Add date range parameters to API calls
- [ ] Update frontend to send selected timeframe to backend
- [ ] Implement efficient data filtering (backend preferred over frontend)
- [ ] Add loading states during timeframe changes

**API Endpoint Update**:
```
GET /api/pmc-metrics?timeframe=30&start_date=2024-12-11&end_date=2025-01-10
```

**Frontend State Management**:
- Track selected timeframe in component state
- Trigger API call on timeframe change
- Cache results to minimize API calls

### 4. MEDIUM: X-Axis Labels and Ticks
**Issue**: X-axis lacks proper labels and ticks for date representation.

**Technical Implementation**:
- [ ] Implement smart date labeling based on selected timeframe
- [ ] For ≤30 days: Show daily ticks
- [ ] For >30 days: Show weekly/monthly ticks to prevent overcrowding
- [ ] Ensure proper date formatting and readability
- [ ] Add date range display above chart

**Chart Configuration**:
```javascript
xAxis: {
  type: 'time',
  labels: {
    format: timeframe <= 30 ? 'MMM DD' : 'MMM YYYY',
    step: timeframe <= 30 ? 1 : Math.ceil(timeframe / 30)
  }
}
```

### 5. MEDIUM: Y-Axis Visibility Fix
**Issue**: Y-axes are cut off and need proper display.

**Technical Implementation**:
- [ ] Adjust chart container padding/margins
- [ ] Ensure axis labels have sufficient space
- [ ] Fix axis title positioning and rotation
- [ ] Validate chart dimensions and responsive behavior

**CSS/Chart Configuration**:
```css
.chart-container {
  padding: 20px 40px 40px 60px; /* top right bottom left */
  margin: 20px;
}
```

### 6. LOW: Remove Unnecessary UI Elements
**Issue**: Left and right arrows in top banner serve no purpose.

**Technical Implementation**:
- [ ] Remove arrow elements from PMC header
- [ ] Clean up associated CSS/styling
- [ ] Ensure layout remains balanced after removal

### 7. LOW: Collapsible Metrics Selection
**Issue**: Select Metrics section should be collapsible to simplify screen.

**Technical Implementation**:
- [ ] Implement simple show/hide toggle for metrics section
- [ ] Use minimal state management (boolean toggle)
- [ ] Ensure smooth animation/transition
- [ ] Maintain selected metrics state when collapsed

**Implementation Approach**:
```javascript
const [metricsVisible, setMetricsVisible] = useState(true);
// Simple toggle with minimal re-renders
```

### 8. LOW: Layout Simplification
**Issue**: Multiple container layers complicate the plot area.

**Technical Implementation**:
- [ ] Audit and reduce unnecessary div containers
- [ ] Simplify CSS hierarchy and nesting
- [ ] Optimize chart container structure
- [ ] Maintain responsive design while reducing complexity

## Technical Requirements

### Performance Considerations
- Minimize API calls through smart caching
- Implement efficient data filtering on backend
- Use React.memo for chart components to prevent unnecessary re-renders
- Optimize chart library configuration for large datasets

### Data Flow Architecture
```
Database → Backend API → Frontend State → Chart Component → Chart Library
```

### Error Handling
- Add proper error boundaries for chart components
- Implement fallback UI for missing data
- Add user-friendly error messages
- Log errors for debugging

### Testing Strategy
- Unit tests for data transformation functions
- Integration tests for API endpoints
- Component tests for chart rendering
- End-to-end tests for user interactions

## Success Criteria
- [ ] PMC chart displays all expected data lines (CTL, ATL, TSB, Daily TSS)
- [ ] Timeframe selection updates chart data correctly
- [ ] X-axis shows appropriate date labels
- [ ] Y-axes are fully visible and properly labeled
- [ ] Data freshness timestamp is displayed
- [ ] UI is simplified and responsive
- [ ] No unnecessary API calls during user interactions

## Implementation Order
1. Data connection investigation (blocking issue)
2. Backend data freshness and timestamp
3. Timeframe functionality
4. Chart axis fixes
5. UI cleanup and simplification
6. Performance optimization
7. Testing and validation

## Notes
- Focus on backend-first approach for data filtering to minimize frontend processing
- Maintain existing chart library (appears to be a line chart implementation)
- Ensure responsive design works across different screen sizes
- Document any API changes for future reference 