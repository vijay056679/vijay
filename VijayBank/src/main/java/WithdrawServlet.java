

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/WithdrawServlet")
public class WithdrawServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
    
    public WithdrawServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
		PrintWriter pw=response.getWriter();
		
		
		int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
		int amt=Integer.parseInt(request.getParameter("amountwithdraw"));
		
		try
		{
			Class.forName("oracle.jdbc.driver.OracleDriver");
			String url="jdbc:oracle:thin:@localhost:1521:xe";
			Connection con=DriverManager.getConnection(url,"system","056679");
			
			String sql1="select balance from Account where accountnumber=?";
			
			PreparedStatement ps=con.prepareStatement(sql1);
			ps.setInt(1, accountnumber );
			ResultSet rs=ps.executeQuery();
			
			if(rs.next())
			{
				if(amt<=rs.getInt(1))
				{
					pw.println("Collect Cash"+amt);
					String sql2="update Account set balance = balance-? where accountnumber=?";
					PreparedStatement ps1=con.prepareStatement(sql2);
					ps1.setInt(1, amt );
					ps1.setInt(2, accountnumber);
					int count=ps1.executeUpdate();
					if(count>0)
					{
						pw.println("Updated");
						response.setContentType("text/html");
						RequestDispatcher rd=request.getRequestDispatcher("Service.html");
						rd.include(request, response);					}
					else
					{
						pw.println("Failed");
						response.setContentType("text/html");
						RequestDispatcher rd=request.getRequestDispatcher("Service.html");
						rd.include(request, response);
					}
				}
				else
				{
					pw.println("Low Balance Error");
					response.setContentType("text/html");
					RequestDispatcher rd=request.getRequestDispatcher("Service.html");
					rd.include(request, response);
				}
			}
			else
			{
				pw.println("No Such Record");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("withdraw_form");
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
