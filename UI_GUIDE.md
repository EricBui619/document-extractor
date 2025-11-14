# UI Enhancement Guide

## New Features in the Sidebar

### 1. Page Selection Section

Located at the top of the sidebar, this section allows you to choose which pages to extract:

```
┌─────────────────────────────────────┐
│ ⚙️ Settings                         │
├─────────────────────────────────────┤
│ ✓ OpenAI API Key loaded from .env  │
├─────────────────────────────────────┤
│                                     │
│ 📄 Page Selection                   │
│                                     │
│ Select pages to extract:            │
│ ○ All pages                         │
│ ○ Specific pages                    │
│ ○ Page range                        │
│                                     │
│ 📊 Total pages in PDF: 25           │
│                                     │
└─────────────────────────────────────┘
```

#### Mode 1: All Pages (Default)
Simply processes the entire PDF - no additional input needed.

#### Mode 2: Specific Pages
```
┌─────────────────────────────────────┐
│ Select pages to extract:            │
│ ○ All pages                         │
│ ● Specific pages                    │
│ ○ Page range                        │
│                                     │
│ 📊 Total pages in PDF: 25           │
│                                     │
│ Enter page numbers (comma-separated)│
│ ┌─────────────────────────────────┐ │
│ │ 1, 3, 5, 7                      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ✓ Will process 4 page(s):          │
│   [1, 3, 5, 7]                      │
└─────────────────────────────────────┘
```

**Features:**
- Enter pages separated by commas
- Automatically filters out invalid page numbers
- Removes duplicates
- Shows preview of pages that will be processed

**Example inputs:**
- `1, 5, 10` → Processes pages 1, 5, and 10
- `1,2,3,5,7,11` → Processes pages 1, 2, 3, 5, 7, 11
- `1, 100, 5` (PDF has 25 pages) → Processes pages 1 and 5 (filters out 100)

#### Mode 3: Page Range
```
┌─────────────────────────────────────┐
│ Select pages to extract:            │
│ ○ All pages                         │
│ ○ Specific pages                    │
│ ● Page range                        │
│                                     │
│ 📊 Total pages in PDF: 25           │
│                                     │
│ ┌──────────┐  ┌──────────┐         │
│ │From page:│  │ To page: │         │
│ │    5     │  │    15    │         │
│ └──────────┘  └──────────┘         │
│                                     │
│ ✓ Will process 11 page(s)           │
│   from 5 to 15                      │
└─────────────────────────────────────┘
```

**Features:**
- Use number inputs for start and end pages
- Validates that start ≤ end
- Shows page count preview
- Bounded by actual PDF page count

**Example ranges:**
- Pages 1-5 → Processes first 5 pages
- Pages 10-15 → Processes 6 pages (10, 11, 12, 13, 14, 15)
- Pages 20-25 → Processes last 6 pages

---

### 2. Performance Options Section

Control how many pages are processed simultaneously:

```
┌─────────────────────────────────────┐
│ 🚀 Performance Options               │
│                                     │
│ Parallel Processing Threads         │
│ ├─────●─────┬─────┬─────┬─────┤   │
│ 1           4     6     8          │
│                                     │
│ Number of pages to process          │
│ simultaneously. More threads =      │
│ faster but higher API rate limit    │
│ usage                               │
└─────────────────────────────────────┘
```

**Slider Range:** 1-8 threads
**Default:** 4 threads
**Recommended:**
- Small PDFs (1-5 pages): 2-4 threads
- Medium PDFs (5-20 pages): 4-6 threads
- Large PDFs (20+ pages): 6-8 threads
- Rate limit concerns: 1-2 threads

**Performance Impact:**
```
Threads → Speed
   1   → ~20s per page (sequential)
   2   → ~10s per page (2x faster)
   4   → ~5s per page  (4x faster)
   8   → ~2-3s per page (6-8x faster)
```

---

## Complete Sidebar Layout

```
┌─────────────────────────────────────┐
│ ⚙️ Settings                         │
├─────────────────────────────────────┤
│ ✓ OpenAI API Key loaded from .env  │
├─────────────────────────────────────┤
│                                     │
│ 📄 Page Selection                   │
│ [Radio buttons for mode selection]  │
│ [Dynamic inputs based on mode]      │
│ [Preview of pages to process]       │
│                                     │
├─────────────────────────────────────┤
│                                     │
│ 🚀 Performance Options               │
│ [Thread slider: 1-8]                │
│                                     │
├─────────────────────────────────────┤
│                                     │
│ ⚙️ Processing Options                │
│ [DPI slider: 150-600]               │
│ [✓] Refine Table Structures         │
│ [✓] Extract Embedded Images         │
│ [Dropdown: HTML to PDF Method]      │
│                                     │
├─────────────────────────────────────┤
│                                     │
│ 📚 About                             │
│ [Information about the tool]        │
│                                     │
└─────────────────────────────────────┘
```

---

## Usage Examples

### Example 1: Quick Test (Extract First Page)
1. Upload your PDF
2. Select "Specific pages"
3. Enter: `1`
4. Set threads to 1
5. Click "Process PDF"

**Result:** Fast extraction of just the first page for testing

---

### Example 2: Extract Summary Pages
1. Upload annual report (100 pages)
2. Select "Specific pages"
3. Enter: `1, 2, 50, 99, 100` (cover, TOC, financial summary, conclusion, back cover)
4. Set threads to 4
5. Click "Process PDF"

**Result:** Extract only key pages, saving time and API costs

---

### Example 3: Extract Chapter
1. Upload book (500 pages)
2. Select "Page range"
3. From: 45, To: 75 (Chapter 3)
4. Set threads to 8
5. Click "Process PDF"

**Result:** Fast extraction of entire chapter with maximum parallelization

---

### Example 4: Full Document (Optimized)
1. Upload document (25 pages)
2. Select "All pages"
3. Set threads to 6
4. Click "Process PDF"

**Result:** Full document processed with good parallelization

---

## Visual Feedback

### Before Upload
```
┌─────────────────────────────────────┐
│ 📄 Page Selection                   │
│                                     │
│ [Radio buttons]                     │
│                                     │
│ 📤 Upload a PDF to select pages     │
└─────────────────────────────────────┘
```

### After Upload
```
┌─────────────────────────────────────┐
│ 📄 Page Selection                   │
│                                     │
│ ○ All pages                         │
│ ● Specific pages                    │
│ ○ Page range                        │
│                                     │
│ 📊 Total pages in PDF: 25           │
│                                     │
│ [Input field appears]               │
│                                     │
│ ✓ Will process 3 page(s): [1,5,10] │
└─────────────────────────────────────┘
```

### Invalid Input
```
│ Enter page numbers:                 │
│ ┌─────────────────────────────────┐ │
│ │ abc, xyz                        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ✗ Invalid input. Please enter       │
│   numbers separated by commas       │
```

### Out of Bounds
```
│ Enter page numbers:                 │
│ ┌─────────────────────────────────┐ │
│ │ 1, 100, 200                     │ │
│ └─────────────────────────────────┘ │
│ (PDF has 25 pages)                  │
│                                     │
│ ✓ Will process 1 page(s): [1]       │
│ (100 and 200 filtered out)          │
```

---

## Processing Flow

### Step-by-Step

1. **Upload PDF**
   ```
   📤 Upload PDF
   ┌─────────────────────────────────┐
   │ Drag and drop PDF here          │
   │ or click to browse              │
   └─────────────────────────────────┘
   ```

2. **Configure Settings**
   ```
   Sidebar automatically shows:
   - Total page count
   - Page selection options
   - Thread configuration
   ```

3. **Select Pages**
   ```
   Choose one of:
   - All pages → Process entire PDF
   - Specific pages → Enter page numbers
   - Page range → Select range
   ```

4. **Set Performance**
   ```
   Adjust threads based on:
   - PDF size
   - Time constraints
   - API rate limit concerns
   ```

5. **Process**
   ```
   Click "🚀 Process PDF"

   Progress shown:
   🔄 Processed 3/5 pages
   [████████░░] 60%
   ```

6. **Results**
   ```
   ✅ Processing Complete!

   📊 Extraction Statistics
   Pages: 5 | Tables: 12 | Images: 8

   📥 Download Results
   [Download PDF] [Download Report]
   ```

---

## Tips & Best Practices

### For Speed
- Use maximum threads (8) for large PDFs
- Select only needed pages
- Increase DPI only when necessary

### For Accuracy
- Use default settings (4 threads, 300 DPI)
- Enable table refinement
- Extract embedded images

### For Cost Savings
- Extract only required pages
- Use lower DPI for drafts (150)
- Skip table refinement for simple documents

### For Testing
- Start with 1-2 pages
- Use 1 thread for debugging
- Enable all refinement options

---

## Troubleshooting

### "No valid page numbers entered"
**Cause:** All entered pages are out of bounds
**Solution:** Check PDF page count, enter valid numbers

### "Invalid input"
**Cause:** Non-numeric characters in page input
**Solution:** Enter only numbers and commas (e.g., 1, 5, 10)

### Slow Processing
**Cause:** Low thread count or large page selection
**Solution:** Increase threads or reduce page selection

### API Rate Limit Errors
**Cause:** Too many parallel threads
**Solution:** Reduce threads to 1-2

---

## Keyboard Shortcuts

While in sidebar inputs:
- `Tab` - Navigate between fields
- `Enter` - Apply selection
- `Arrows` - Adjust sliders
- `Cmd/Ctrl + A` - Select all text in input

---

## Mobile/Tablet View

The sidebar collapses on smaller screens:
- Tap hamburger menu (☰) to open sidebar
- All functionality remains the same
- Inputs stack vertically for easier access

---

This completes the UI enhancement guide. All features are intuitive and include real-time validation and feedback!
