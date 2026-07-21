with open('database.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

out = []
for line in lines:
    if line.strip() == '# Seed Clusters across Campus & Community':
        break
    out.append(line)

out.extend([
    '    conn.commit()',
    '',
    'if __name__ == "__main__":',
    '    init_db()',
    '    print("Database multi-tenancy initialized.")',
    ''
])

with open('database.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
