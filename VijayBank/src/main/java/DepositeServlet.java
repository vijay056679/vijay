

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;


import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/DepositeServlet")
public class DepositeServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
       
    
    public DepositeServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
		
		PrintWriter pw=response.getWriter();
		
		int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
		int amt=Integer.parseInt(request.getParameter("amountdeposit"));
		
		try
		{
			Class.forName("oracle.jdbc.driver.OracleDriver");
			String url="jdbc:oracle:thin:@localhost:1521:xe";
			Connection con=DriverManager.getConnection(url,"system","056679");
			
			String sql="update Account set balance= balance + ? where accountnumber= ?";
			
			PreparedStatement ps=con.prepareStatement(sql);
			
			ps.setInt(1, amt );
			ps.setInt(2, accountnumber);
			
			int count=ps.executeUpdate();
			
			if(count>0)
			{
				pw.println("Deposited");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("Service.html");
				rd.include(request, response);
			}
			else
			{
				pw.println("Invalid Account Number");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("deposit_form");
				rd.include(request, response);
			}
			con.close();
			
          }
		catch(Exception e)
		{
			pw.println(e.getMessage());
		}
	}
}
	
	


