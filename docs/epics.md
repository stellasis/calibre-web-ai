# calibre-web-ai - Epic Breakdown

**Author:** Sam
**Date:** 2025-01-27
**Project Level:** web-application
**Target Scale:** MVP (Week 1)

---

## Overview

This document provides the complete epic and story breakdown for calibre-web-ai, decomposing the requirements from the [PRD](./prd.md) into implementable stories with full context from [Architecture](./architecture.md) and [UX Design](./ux-integration-guide.md).

**Living Document Notice:** This document incorporates all available context (PRD + Architecture + UX) to create comprehensive, implementation-ready stories.

**Document Structure:** This master index provides an overview and links to detailed epic files. Each epic is documented in its own file in the `epics/` directory for easier navigation and maintenance.

---

## Functional Requirements Inventory

**FR1: AI Summary Generation**
- On-demand summary generation for individual books
- Uses metadata + first 20 pages/chapter text
- Cached summaries stored in database
- Admin bulk generation capability
- **Coverage:** Epic 1 (Foundation), Epic 2 (AI Summary Feature)

**FR2: AI Semantic Search**
- Natural language query processing
- Vector similarity search using sqlite-vss
- Fallback to metadata embeddings when summaries unavailable
- Integration with existing search UI
- **Coverage:** Epic 1 (Foundation), Epic 3 (AI Search Feature)

**FR3: Similar Books Recommendations**
- Nearest neighbor search in embedding space
- Display on book detail page
- Reuses same embedding store as search
- **Coverage:** Epic 1 (Foundation), Epic 4 (Similar Books Feature)

**FR4: Configuration Management**
- Master toggle for all AI features
- Provider/model configuration
- API key management
- Admin UI for configuration
- **Coverage:** Epic 1 (Foundation), Epic 5 (Configuration UI)

**FR5: Background Job System**
- Summary generation jobs
- Embedding generation jobs
- Bulk operations support
- **Coverage:** Epic 1 (Foundation), Epic 2 (AI Summary Feature)

---

## FR Coverage Map

**FR1 → Epic 1 (Stories 1.1-1.5), Epic 2 (Stories 2.1-2.4)**
**FR2 → Epic 1 (Stories 1.1-1.5), Epic 3 (Stories 3.1-3.3)**
**FR3 → Epic 1 (Stories 1.1-1.5), Epic 4 (Stories 4.1-4.2)**
**FR4 → Epic 1 (Stories 1.1-1.5), Epic 5 (Stories 5.1-5.2)**
**FR5 → Epic 1 (Stories 1.1-1.5), Epic 2 (Stories 2.1-2.4)**

---

## Epic Structure

### Epic 1: Foundation Setup
**User Value Statement:** Establishes the technical infrastructure needed for all AI features, enabling users to configure and use AI capabilities.

**Stories:** 5 stories (1.1-1.5)
- Story 1.1: Database Schema and Models
- Story 1.2: sqlite-vss Extension Setup
- Story 1.3: Configuration Management Infrastructure
- Story 1.4: Text Extraction Service
- Story 1.5: Background Task Base Infrastructure

**PRD Coverage:** FR4 (Configuration Management), FR5 (Background Job System) - foundational support for all features

**Dependencies:** None (foundation epic)

**📄 [View Epic 1 Details →](epics/epic-1-foundation.md)**

---

### Epic 2: AI Summary Feature
**User Value Statement:** Users can generate and view AI-powered summaries of books to quickly understand what they're about.

**Stories:** 4 stories (2.1-2.4)
- Story 2.1: AI Summarization Service
- Story 2.2: Background Task for Summary Generation
- Story 2.3: API Endpoint for Summary Generation
- Story 2.4: UI Integration for Summary Generation

**PRD Coverage:** FR1 (AI Summary Generation)

**Dependencies:** Epic 1 (Foundation Setup)

**📄 [View Epic 2 Details →](epics/epic-2-summary.md)**

---

### Epic 3: AI Semantic Search
**User Value Statement:** Users can search for books using natural language queries and get results ranked by semantic similarity.

**Stories:** 3 stories (3.1-3.3)
- Story 3.1: Embedding Generation Service
- Story 3.2: Semantic Search Service
- Story 3.3: Search Route Integration and UI

**PRD Coverage:** FR2 (AI Semantic Search)

**Dependencies:** Epic 1 (Foundation Setup), Epic 2 (AI Summary Feature - for embeddings)

**📄 [View Epic 3 Details →](epics/epic-3-search.md)**

---

### Epic 4: Similar Books Recommendations
**User Value Statement:** Users can discover similar books on the detail page, helping them find related content to explore.

**Stories:** 2 stories (4.1-4.2)
- Story 4.1: Similar Books API Endpoint
- Story 4.2: Similar Books UI Integration

**PRD Coverage:** FR3 (Similar Books Recommendations)

**Dependencies:** Epic 1 (Foundation Setup), Epic 2 (AI Summary Feature - for embeddings), Epic 3 (AI Semantic Search - reuses search infrastructure)

**📄 [View Epic 4 Details →](epics/epic-4-similar-books.md)**

---

### Epic 5: Configuration UI
**User Value Statement:** Administrators can configure AI features, set API keys, and manage provider settings through a user-friendly interface.

**Stories:** 2 stories (5.1-5.2)
- Story 5.1: Admin Configuration Display
- Story 5.2: Admin Configuration Edit Page

**PRD Coverage:** FR4 (Configuration Management - UI component)

**Dependencies:** Epic 1 (Foundation Setup - configuration infrastructure)

**📄 [View Epic 5 Details →](epics/epic-5-configuration.md)**

---

## FR Coverage Matrix

**FR1: AI Summary Generation**
- ✅ Epic 1.4 (Text Extraction) - Enables text extraction for summaries
- ✅ Epic 2.1 (Summarization Service) - Core summary generation
- ✅ Epic 2.2 (Background Task) - Async summary generation
- ✅ Epic 2.3 (API Endpoint) - User-triggered generation
- ✅ Epic 2.4 (UI Integration) - User interface for summaries

**FR2: AI Semantic Search**
- ✅ Epic 1.2 (sqlite-vss) - Vector search infrastructure
- ✅ Epic 3.1 (Embedding Generation) - Book embeddings for search
- ✅ Epic 3.2 (Semantic Search Service) - Core search functionality
- ✅ Epic 3.3 (Search Route Integration) - User-facing search feature

**FR3: Similar Books Recommendations**
- ✅ Epic 3.1 (Embedding Generation) - Book embeddings for similarity
- ✅ Epic 4.1 (Similar Books API) - API endpoint for similar books
- ✅ Epic 4.2 (Similar Books UI) - User interface for similar books

**FR4: Configuration Management**
- ✅ Epic 1.3 (Configuration Infrastructure) - Backend configuration system
- ✅ Epic 5.1 (Admin Configuration Display) - Configuration status display
- ✅ Epic 5.2 (Admin Configuration Edit) - Configuration editing interface

**FR5: Background Job System**
- ✅ Epic 1.5 (Background Task Infrastructure) - Task system integration
- ✅ Epic 2.2 (Summary Generation Task) - Summary background jobs
- ✅ Epic 3.1 (Embedding Generation) - Embedding generation (can be background job)

---

## Summary

**Epic Structure:** 5 epics delivering incremental user value
- Epic 1: Foundation Setup (5 stories) - Technical infrastructure
- Epic 2: AI Summary Feature (4 stories) - User-facing summary generation
- Epic 3: AI Semantic Search (3 stories) - User-facing semantic search
- Epic 4: Similar Books Recommendations (2 stories) - User-facing recommendations
- Epic 5: Configuration UI (2 stories) - Admin configuration interface

**Total Stories:** 16 stories covering all 5 functional requirements

**FR Coverage:** 100% - All functional requirements mapped to specific stories with complete acceptance criteria

**Technical Context:** All stories incorporate Architecture decisions (database, API, background tasks, text extraction, configuration)

**UX Integration:** All user-facing stories incorporate UX Design patterns (templates, JavaScript, Bootstrap components)

**Implementation Ready:** All stories are sized for single dev agent completion with complete acceptance criteria and technical guidance

---

## Final Validation

### FR Coverage Validation ✅

**Complete FR Coverage Matrix:**
- ✅ **FR1 (AI Summary Generation):** Covered by Epic 1.4, 2.1, 2.2, 2.3, 2.4
- ✅ **FR2 (AI Semantic Search):** Covered by Epic 1.2, 3.1, 3.2, 3.3
- ✅ **FR3 (Similar Books Recommendations):** Covered by Epic 3.1, 4.1, 4.2
- ✅ **FR4 (Configuration Management):** Covered by Epic 1.3, 5.1, 5.2
- ✅ **FR5 (Background Job System):** Covered by Epic 1.5, 2.2, 3.1

**Critical Validation:** ✅ Every single FR from the PRD is covered by at least one story with complete acceptance criteria.

### Architecture Integration Validation ✅

**Architecture Decisions Properly Implemented:**
- ✅ **Database Schema:** All stories reference `app_settings` schema, BLOB format for vectors, sqlite-vss virtual table
- ✅ **API Endpoints:** All endpoints follow Architecture section 3.2 patterns (`/api/ai/*` routes)
- ✅ **Data Models:** All models follow Architecture section 3.1 patterns (BookSummary, BookEmbedding in `cps/ub.py`)
- ✅ **Authentication/Authorization:** All routes use `@login_required_if_no_ano` or `@admin_required` (Architecture section 3.2)
- ✅ **Performance Requirements:** Timeouts, retries, background jobs addressed (Architecture section 3.4, 3.5)
- ✅ **Security Measures:** API keys stored securely, feature toggle implemented (Architecture section 3.5)
- ✅ **Error Handling:** Graceful degradation, fallback patterns, proper error responses (Architecture section 3.2)
- ✅ **Integration Points:** All integration points (routes, templates, database) properly specified (Architecture section 4)

### UX Integration Validation ✅

**UX Design Patterns Properly Implemented:**
- ✅ **User Flows:** All user flows follow UX Design section 8 (flow diagrams)
- ✅ **Screen Layouts:** All UI components match UX Design specifications (sections 1-4)
- ✅ **Interaction Patterns:** Button groups, toggles, panels follow UX Design patterns (sections 1-4)
- ✅ **Responsive Behavior:** Grid layouts use Bootstrap breakpoints (UX section 7)
- ✅ **Accessibility Requirements:** ARIA labels, keyboard navigation, screen reader support (UX section 6)
- ✅ **Error States:** Error messages, loading states, feedback patterns implemented (UX sections 1-4)
- ✅ **Form Validation:** Real-time validation, error messages follow UX patterns (UX section 4)
- ✅ **Loading States:** Spinners, progress indicators follow UX patterns (UX section 1)

### Story Quality Validation ✅

**Story Quality Checks:**
- ✅ **Story Sizing:** All stories are sized for single dev agent completion in one focused session
- ✅ **Acceptance Criteria:** All stories have specific, testable acceptance criteria in BDD format
- ✅ **Technical Implementation:** All stories include specific guidance from Architecture document
- ✅ **User Experience:** All user-facing stories include exact interaction patterns from UX Design
- ✅ **Dependencies:** No forward dependencies exist - all prerequisites clearly stated
- ✅ **Epic Sequence:** Epic sequence delivers incremental value (Foundation → Summary → Search → Similar → Config)
- ✅ **Foundation Epic:** Epic 1 properly enables all subsequent work

### Final Quality Check ✅

**Critical Questions Answered:**

1. ✅ **User Value:** Does each epic deliver something users can actually do/use?
   - Epic 1: Enables AI features (infrastructure)
   - Epic 2: Generate and view summaries (user-facing)
   - Epic 3: Semantic search (user-facing)
   - Epic 4: Similar books discovery (user-facing)
   - Epic 5: Configure AI features (admin-facing)

2. ✅ **Completeness:** Are ALL PRD functional requirements covered?
   - All 5 FRs mapped to specific stories with complete acceptance criteria

3. ✅ **Technical Soundness:** Do stories properly implement Architecture decisions?
   - All stories reference specific Architecture sections and follow documented patterns

4. ✅ **User Experience:** Do stories follow UX design patterns?
   - All user-facing stories reference specific UX Design sections and follow documented patterns

5. ✅ **Implementation Ready:** Can dev agents implement these stories autonomously?
   - All stories include complete acceptance criteria, technical notes, prerequisites, and specific file locations

---

## ✅ EPIC AND STORY CREATION COMPLETE

**Output Generated:** 
- Master index: `docs/epics.md`
- Epic files: `docs/epics/epic-1-foundation.md` through `epic-5-configuration.md`

**Full Context Incorporated:**
- ✅ PRD functional requirements and scope
- ✅ Architecture technical decisions and contracts
- ✅ UX Design interaction patterns and specifications

**FR Coverage:** 5 functional requirements mapped to 16 stories across 5 epics
**Epic Structure:** 5 epics delivering incremental user value
**Story Quality:** All stories sized for single dev agent completion with complete acceptance criteria

**Ready for Phase 4:** Sprint Planning and Development Implementation

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document incorporates all available context (PRD + Architecture + UX) to create comprehensive, actionable stories for development._
