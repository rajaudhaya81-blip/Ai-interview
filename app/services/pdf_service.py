import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
try:
    import matplotlib
    # Use the non-interactive Agg backend to avoid GUI issues
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

class PDFReportService:
    @staticmethod
    def generate_radar_chart(skill_breakdown):
        """
        Generates a radar chart using matplotlib and returns a ReportLab Image flowable.
        """
        if not HAS_MATPLOTLIB or not skill_breakdown:
            return None

        # Clean / prepare skills
        labels = list(skill_breakdown.keys())
        values = list(skill_breakdown.values())
        
        num_vars = len(labels)
        if num_vars < 3:
            # Radar chart needs at least 3 axes, fallback to bar chart in memory
            fig, ax = plt.subplots(figsize=(4, 2.5))
            fig.patch.set_facecolor('#ffffff')
            ax.set_facecolor('#f8f9fa')
            bars = ax.barh(labels, values, color='#6200ea')
            ax.set_xlim(0, 100)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#cccccc')
            ax.spines['left'].set_color('#cccccc')
            ax.tick_params(colors='#333333', labelsize=8)
            plt.title("Skill Distribution", color='#1a1a2e', size=10, weight='bold')
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return Image(buf, width=250, height=150)

        # Standard Radar Chart
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        
        # Complete the circular plot loop
        values_loop = values + [values[0]]
        angles_loop = angles + [angles[0]]
        
        fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#f8f9fa')
        
        # Plot and fill outline
        ax.fill(angles_loop, values_loop, color='#6200ea', alpha=0.2)
        ax.plot(angles_loop, values_loop, color='#6200ea', linewidth=1.5)
        
        # Labels and grids
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, color='#333333', size=8, weight='semibold')
        ax.set_rgrids([20, 40, 60, 80, 100], color='#dddddd', size=7)
        ax.set_ylim(0, 100)
        ax.spines['polar'].set_color('#cccccc')
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=220, height=220)

    @classmethod
    def generate_interview_pdf(cls, candidate_name, email, interview, qa_list, report_data):
        """
        Creates a PDF report buffer containing interview summary, scores, radar chart,
        and full question/answer analysis.
        """
        buffer = io.BytesIO()
        
        # Setup document
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=36
        )
        
        story = []
        
        # Styles Setup
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=15
        )
        
        h1_style = ParagraphStyle(
            'H1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#6200ea'),
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'H2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        )

        body_bold_style = ParagraphStyle(
            'BodyBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#777777')
        )

        box_text_style = ParagraphStyle(
            'BoxText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#1a1a2e')
        )

        # 1. Header (Title and Meta)
        story.append(Paragraph("InterviewAI - Performance Report", title_style))
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        meta_text = f"<b>Candidate:</b> {candidate_name} ({email})<br/>" \
                    f"<b>Date:</b> {date_str}<br/>" \
                    f"<b>Interview Type:</b> {interview.type} ({interview.difficulty})<br/>" \
                    f"<b>Interviewer Personality:</b> {interview.personality} | <b>Target Company:</b> {interview.company}"
        story.append(Paragraph(meta_text, meta_style))
        story.append(Spacer(1, 15))
        
        # 2. Score Summary Cards (Table)
        score_table_data = [
            [
                Paragraph("<b>Overall Score</b>", body_style),
                Paragraph("<b>Readiness Score</b>", body_style)
            ],
            [
                Paragraph(f"<font size=20 color='#6200ea'><b>{report_data.get('overall_score', 0)}%</b></font>", body_style),
                Paragraph(f"<font size=20 color='#2e7d32'><b>{report_data.get('readiness_score', 0)}%</b></font>", body_style)
            ]
        ]
        score_table = Table(score_table_data, colWidths=[270, 270])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e0e0e0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0'))
        ]))
        story.append(score_table)
        story.append(Spacer(1, 15))
        
        # 3. Radar Chart & Strengths / Weaknesses side by side
        radar_flowable = cls.generate_radar_chart(report_data.get('skill_breakdown', {}))
        
        strengths_html = "".join([f"• {s}<br/>" for s in report_data.get('strengths', [])])
        weaknesses_html = "".join([f"• {w}<br/>" for w in report_data.get('weaknesses', [])])
        
        details_text = f"<b>Key Strengths:</b><br/>{strengths_html}<br/>" \
                       f"<b>Areas for Improvement:</b><br/>{weaknesses_html}"
        details_para = Paragraph(details_text, box_text_style)
        
        if radar_flowable:
            side_table_data = [[radar_flowable, details_para]]
            side_table = Table(side_table_data, colWidths=[240, 300])
            side_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('RIGHTPADDING', (0,0), (0,0), 10),
                ('LEFTPADDING', (1,0), (1,0), 10),
                ('TOPPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(side_table)
        else:
            story.append(details_para)
            
        story.append(Spacer(1, 15))
        
        # 4. Recommendations & Learning Path
        story.append(Paragraph("Hiring Committee Recommendation", h1_style))
        story.append(Paragraph(report_data.get('recommendations', 'N/A'), body_style))
        story.append(Spacer(1, 10))
        
        # 5. Detailed Question Analysis
        story.append(Paragraph("Detailed Question & Answer Analysis", h1_style))
        story.append(Spacer(1, 5))
        
        for idx, qa in enumerate(qa_list):
            q_num = idx + 1
            question_p = Paragraph(f"<b>Q{q_num}: {qa.get('question_text')}</b>", body_bold_style)
            answer_p = Paragraph(f"<i>Candidate Answer:</i> {qa.get('answer_text', 'No answer submitted.')}", body_style)
            
            # Scores & metrics sub-table
            score_bar = f"<b>Score: {qa.get('score', 0)}/100</b>"
            metrics_line = ""
            if qa.get('accuracy'):
                metrics_line = f" | Accuracy: {qa.get('accuracy')} | Comm: {qa.get('communication')} | Confidence: {qa.get('confidence')}"
            
            eval_p = Paragraph(f"<font color='#6200ea'>{score_bar}{metrics_line}</font>", body_style)
            feedback_p = Paragraph(f"<b>Feedback:</b> {qa.get('feedback', 'N/A')}<br/><b>Tips:</b> {qa.get('improvement_tips', 'N/A')}", box_text_style)
            
            qa_box_data = [
                [question_p],
                [answer_p],
                [eval_p],
                [feedback_p]
            ]
            
            qa_table = Table(qa_box_data, colWidths=[540])
            qa_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
                ('LINEBELOW', (0,0), (0,0), 0.5, colors.HexColor('#f0f0f0')),
                ('LINEBELOW', (0,1), (0,1), 0.5, colors.HexColor('#f0f0f0')),
                ('LINEBELOW', (0,2), (0,2), 0.5, colors.HexColor('#f0f0f0')),
                ('BACKGROUND', (0,3), (0,3), colors.HexColor('#f5f0fa')), # Lavender highlight for feedback
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            
            # Group each Q&A block so it doesn't break across pages awkwardly
            story.append(KeepTogether([qa_table, Spacer(1, 12)]))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
