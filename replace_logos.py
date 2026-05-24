import os

files_to_update = [
    r'e:\Exam Mentor-GPT\frontend\Index\index.html',
    r'e:\Exam Mentor-GPT\frontend\Index\about.html',
    r'e:\Exam Mentor-GPT\frontend\Index\past-papers.html',
    r'e:\Exam Mentor-GPT\frontend\assets\js\layout.js',
    r'e:\Exam Mentor-GPT\frontend\login.html'
]

replacements = {
    '<div class="logo-icon"><i data-lucide="library"></i></div>': '<img src="/assets/img/cropped logo.jpg" alt="ExamMentor Logo" class="custom-logo-img">',
    '<div class="logo-icon-sm"><i data-lucide="brain-circuit"></i></div>': '<img src="/assets/img/cropped logo.jpg" alt="Logo" class="custom-logo-img" style="width:24px; height:24px; padding:1px;">',
    '<div class="brand-logo"><i data-lucide="library" style="width:20px"></i></div>': '<img src="/assets/img/cropped logo.jpg" alt="ExamMentor Logo" class="custom-logo-img" style="width:48px; height:48px; margin-bottom:15px; border-radius:12px;">'
}

for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {os.path.basename(filepath)}')
