from procurement_processors import ProcurementProcessor


def simulate_more(category, seen_ids, page):
    processor = ProcurementProcessor()
    next_page = page + 1

    MAX_RETRIES = 3
    attempt = 0
    new_tenders = []
    candidate_page = next_page
    while attempt < MAX_RETRIES and not new_tenders:
        print(f"Attempt {attempt+1} fetch page {candidate_page}")
        candidate = processor.get_procurements_by_category(category, limit=10, exclude_ids=seen_ids, page=candidate_page)
        print(f"Candidate fetched: {len(candidate)} items")

        filtered_candidate = []
        for t in candidate:
            t_id = t.get('tender_id', '') or t.get('tender_name', '')
            t_key = f"{t.get('tender_name','')}|{t.get('org_name','')}"
            if t_id in seen_ids or t_key in seen_ids:
                continue
            filtered_candidate.append(t)

        if filtered_candidate:
            new_tenders = filtered_candidate[:10]
            print(f"Found {len(new_tenders)} filtered tenders from page {candidate_page}")
            break

        attempt += 1
        candidate_page += 1

    if not new_tenders:
        print("Fallback to multi-day query")
        new_tenders = processor.get_procurements_by_category(category, limit=10, exclude_ids=seen_ids)
    return new_tenders


if __name__ == '__main__':
    proc = ProcurementProcessor()
    first = proc.get_procurements_by_category('工程類', limit=10)
    ids = [t.get('tender_id', '') or t.get('tender_name', '') for t in first]
    print('First page count', len(first))
    more = simulate_more('工程類', ids, page=1)
    print('More page count', len(more))
    overlap = set(ids) & set([t.get('tender_id', '') or t.get('tender_name', '') for t in more])
    print('Overlap:', len(overlap))