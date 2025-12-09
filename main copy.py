import ast
import difflib


class ASTComparator:
    def __init__(self, original_file, modified_file):
        self.original_file = original_file
        self.modified_file = modified_file
        
        with open(original_file, 'r') as f1:
            self.original_code = f1.read()
            self.original_tree = ast.parse(self.original_code)
        
        with open(modified_file, 'r') as f2:
            self.modified_code = f2.read()
            self.modified_tree = ast.parse(self.modified_code)
    
    def get_node_signature(self, node):
        return ast.dump(node, annotate_fields=True, include_attributes=False)
    
    def get_node_info(self, node, code):
        location = None
        if hasattr(node, 'lineno'):
            location = {
                'lineno': node.lineno,
                'col_offset': node.col_offset,
                'end_lineno': getattr(node, 'end_lineno', node.lineno),
                'end_col_offset': getattr(node, 'end_col_offset', node.col_offset)
            }
        
        code_snippet = self.get_source_segment(code, location) if location else None
        
        return {
            'signature': self.get_node_signature(node),
            'location': location,
            'code': code_snippet,
            'node_type': node.__class__.__name__
        }
    
    def get_source_segment(self, code, location):
        if not location:
            return None
        
        lines = code.splitlines()
        start = location['lineno'] - 1
        end = location.get('end_lineno', location['lineno']) - 1
        
        if start < len(lines):
            if start == end:
                return lines[start]
            else:
                return '\n'.join(lines[start:end+1])
        return None
    
    def compare_with_location(self):
        original_nodes = [self.get_node_info(node, self.original_code) 
                         for node in self.original_tree.body]
        modified_nodes = [self.get_node_info(node, self.modified_code) 
                         for node in self.modified_tree.body]
        
        original_sigs = [node['signature'] for node in original_nodes]
        modified_sigs = [node['signature'] for node in modified_nodes]
        
        matcher = difflib.SequenceMatcher(None, original_sigs, modified_sigs)
        
        changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            elif tag == 'delete':
                for idx in range(i1, i2):
                    node_info = original_nodes[idx]
                    changes.append({
                        'type': 'DELETED',
                        'original_position': idx,
                        'modified_position': None,
                        'original_location': node_info['location'],
                        'modified_location': None,
                        'original_code': node_info['code'],
                        'modified_code': None,
                        'node_type': node_info['node_type']
                    })
            
            elif tag == 'insert':
                for idx in range(j1, j2):
                    node_info = modified_nodes[idx]
                    changes.append({
                        'type': 'ADDED',
                        'original_position': None,
                        'modified_position': idx,
                        'original_location': None,
                        'modified_location': node_info['location'],
                        'original_code': None,
                        'modified_code': node_info['code'],
                        'node_type': node_info['node_type']
                    })
            
            elif tag == 'replace':
                for orig_idx, mod_idx in zip(range(i1, i2), range(j1, j2)):
                    orig_info = original_nodes[orig_idx]
                    mod_info = modified_nodes[mod_idx]
                    changes.append({
                        'type': 'MODIFIED',
                        'original_position': orig_idx,
                        'modified_position': mod_idx,
                        'original_location': orig_info['location'],
                        'modified_location': mod_info['location'],
                        'original_code': orig_info['code'],
                        'modified_code': mod_info['code'],
                        'node_type': f"{orig_info['node_type']} → {mod_info['node_type']}"
                    })
                
                if i2 - i1 > j2 - j1:
                    for idx in range(orig_idx + 1, i2):
                        node_info = original_nodes[idx]
                        changes.append({
                            'type': 'DELETED',
                            'original_position': idx,
                            'modified_position': None,
                            'original_location': node_info['location'],
                            'modified_location': None,
                            'original_code': node_info['code'],
                            'modified_code': None,
                            'node_type': node_info['node_type']
                        })
                elif j2 - j1 > i2 - i1:
                    for idx in range(mod_idx + 1, j2):
                        node_info = modified_nodes[idx]
                        changes.append({
                            'type': 'ADDED',
                            'original_position': None,
                            'modified_position': idx,
                            'original_location': None,
                            'modified_location': node_info['location'],
                            'original_code': None,
                            'modified_code': node_info['code'],
                            'node_type': node_info['node_type']
                        })
        
        return changes
    
    def print_differences(self):
        """변경사항을 읽기 쉽게 출력"""
        changes = self.compare_with_location()
        
        if not changes:
            print("✓ No differences found. Files are logically identical.")
            return
        
        print(f"\n{'='*70}")
        print(f"Comparing: {self.original_file} (ORIGINAL) → {self.modified_file} (MODIFIED)")
        print(f"{'='*70}\n")
        
        for i, change in enumerate(changes, 1):
            change_type = change['type']
            
            if change_type == 'DELETED':
                print(f"[{i}] DELETED")
                # print(f"    Original Position: {change['original_position']}")
                print(f"    Original Line: {change['original_location']['lineno']}")
                # print(f"    Node Type: {change['node_type']}")
                print(f"    Code:")
                for line in change['original_code'].split('\n'):
                    print(f"      - {line}")
                
            elif change_type == 'ADDED':
                print(f"[{i}] ADDED")
                # print(f"    Modified Position: {change['modified_position']}")
                print(f"    Modified Line: {change['modified_location']['lineno']}")
                # print(f"    Node Type: {change['node_type']}")
                print(f"    Code:")
                for line in change['modified_code'].split('\n'):
                    print(f"      + {line}")
                
            elif change_type == 'MODIFIED':
                print(f"[{i}] MODIFIED")
                # print(f"    Position: {change['original_position']} → {change['modified_position']}")
                print(f"    Line: {change['original_location']['lineno']} → {change['modified_location']['lineno']}")
                # print(f"    Node Type: {change['node_type']}")
                print(f"    Original Code:")
                for line in change['original_code'].split('\n'):
                    print(f"      - {line}")
                print(f"    Modified Code:")
                for line in change['modified_code'].split('\n'):
                    print(f"      + {line}")
            
            print()
        
        deleted = sum(1 for c in changes if c['type'] == 'DELETED')
        added = sum(1 for c in changes if c['type'] == 'ADDED')
        modified = sum(1 for c in changes if c['type'] == 'MODIFIED')
        
        print(f"{'='*70}")
        print(f"Summary: {deleted} deleted, {added} added, {modified} modified")
        print(f"{'='*70}")


if __name__ == "__main__":
    comparator = ASTComparator('./test/file1.py', './test/file2.py')
    comparator.print_differences()
